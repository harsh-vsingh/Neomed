import os
import json
import re
import time
from typing import List, Dict, Any
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
    
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", # Changed to 2.5-flash for better availability
    temperature=0.2,
    google_api_key=GEMINI_API_KEY
)

# ...existing code...
JSON_SCHEMA = {
    "patient_demographics": {"age": "string [N]", "sex": "string [N]"},
    "chief_complaint": "string [N]",
    "history_of_present_illness": "narrative paragraph with [N] after every claim",
    "past_medical_history": ["item [N]", "item [N]"],
    "medications": [{"name": "string", "dosage": "string", "citations": "[N]"}],
    "allergies": ["item [N]"],
    "procedures": ["item [N]"],
    "diagnostic_findings": ["item [N]"],
    "assessment": "final diagnosis [N]",
    "plan": "next steps [N]",
    "clinical_course": "chronological narrative with [N] after every sentence"
}

EXAMPLE_SUMMARY = {
    "patient_demographics": {"age": "62 year old [1]", "sex": "male [1]"},
    "chief_complaint": "Chest pain [2]",
    "history_of_present_illness": "Patient presented with acute crushing chest pain [2] that began 2 hours prior to arrival [15]. Pain was associated with nausea [16].",
    "past_medical_history": ["Coronary artery disease [3]", "Hypertension [4]"],
    "medications": [
        {"name": "Aspirin", "dosage": "81mg daily", "citations": "[5]"},
        {"name": "Lisinopril", "dosage": "20mg daily", "citations": "[6]"}
    ],
    "allergies": ["Penicillin [7]"],
    "procedures": ["Cardiac catheterization [8]", "Stent placement to LAD [9]"],
    "diagnostic_findings": ["ST elevation on EKG [10]", "Troponin elevated at 2.5 [11]"],
    "assessment": "Acute Myocardial Infarction [12]",
    "plan": "Start dual antiplatelet therapy [13] and transfer to Cardiac ICU [14]",
    "clinical_course": "Patient stabilized after catheterization [8]. Vital signs remained stable overnight [17]. Improvement noted on Day 2 [18]."
}


prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a Medical Documentation AI assistant for physicians. Generate a structured clinical summary from extracted medical entities.

### OUTPUT FORMAT
Return ONLY valid JSON matching this schema:
{json_schema}

### CITATION RULES
1. Every fact requires EXACTLY ONE citation: "chest pain [5]"
2. If multiple entities share the same citation ID in input, combine them with one citation at end: "diabetes and hypertension [3]"
3. Never use multiple citations for one fact: NO "[1][2]" or "[1], [2]"
4. Only use citation IDs from this list: {citation_ids}
5. For medications, put citation in "citations" field only, not in name/dosage

### MEDICAL CONTENT RULES
1. Process mixed document types (ED notes, discharge summaries, progress notes, consults)
2. Keep medical abbreviations as-is (SOB, CHF, etc)
3. If nearby entities are clinically related and share similar context, combine them into one phrase with shared citation
4. When same finding appears with different citations, keep only the FIRST occurrence
5. For inferred clinical conclusions from multiple entities, use the primary entity's citation
6. Include negations as stated: "denies chest pain [8]"
7. Treat all entities equally regardless of confidence scores
8. If entity lacks clear context, include the raw text with its citation

### SECTION GUIDELINES
- patient_demographics: Extract age and sex if available, otherwise null
- chief_complaint: Primary reason for visit, single sentence
- history_of_present_illness: Chronological narrative, one citation per sentence or claim
- past_medical_history: List format, one item per condition
- medications: List with name, dosage, citations fields
- allergies: List format
- procedures: List format, chronological if dates available
- diagnostic_findings: List format for labs, imaging, vitals
- assessment: Working diagnosis or impression
- plan: Treatment plan and next steps
- clinical_course: Temporal narrative of patient progression

### EXAMPLE
{example}

Use ONLY the provided entities. Do not add external medical knowledge."""),
    
    ("human", """### EXTRACTED ENTITIES BY DATE

Each citation group below contains entities that were found together or are contextually related.
All entities on the same line share that citation ID.

{entities}

Generate the JSON summary. Use one citation per fact. Combine related entities from the same citation group.""")
])

output_parser = JsonOutputParser()
chain = prompt_template | llm | output_parser

# --- NEW SANITIZATION CODE STARTS HERE ---
_citation_dup_pattern1 = re.compile(r'(\[\d+\])(?:\s*,?\s*\[\d+\])+') # Matches [1], [2] or [1][2]
_citation_dup_pattern2 = re.compile(r'\[(\d+)(?:,\s*\d+)+\]')        # Matches [1, 2, 3]

def _collapse_multi_citations_in_string(value: str) -> str:
    """
    Finds patterns like [1][2], [1], [2], or [1,2,3] and replaces them 
    with just the first citation found.
    """
    if not isinstance(value, str):
        return value
        
    # Case 1: [1][2] or [1], [2] -> keeps [1]
    value = _citation_dup_pattern1.sub(r'\1', value)
    
    # Case 2: [1, 2, 3] -> (logic to keep first)
    # This regex logic is tricky with substitution, so we use a callback
    def replace_comma_list(match):
        # Extract the first number
        first_num = match.group(1)
        return f"[{first_num}]"
        
    value = _citation_dup_pattern2.sub(replace_comma_list, value)
    
    return value

def _sanitize_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively walks the JSON and fixes citation strings."""
    def walk(v):
        if isinstance(v, str):
            return _collapse_multi_citations_in_string(v)
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, dict):
            # Special handling for medications 'citations' field
            return {
                k: (walk(v[k]) if k != "citations" else _collapse_multi_citations_in_string(v[k])) 
                for k in v
            }
        return v
    
    return walk(summary)
# --- NEW SANITIZATION CODE ENDS HERE ---

def format_entities_for_prompt(timeline: List[Dict[str, Any]]) -> str:
    # ...existing code...
    """
    Format entities to make it CRYSTAL CLEAR that all entities on one line share ONE citation.
    """
    formatted_lines = []
    
    for date_chunk in timeline:
        date = date_chunk["date"]
        formatted_lines.append(f"\n{'='*60}")
        formatted_lines.append(f"Date: {date}")
        formatted_lines.append(f"{'='*60}")
        
        for entity_group in date_chunk["entities"]:
            if isinstance(entity_group, dict):
                citation_id = entity_group.get("citation_id")
                
                # Get all entity texts in this group
                entity_texts = [e.get("text", "") for e in entity_group.get("entities", [])]
                entity_labels = [e.get("label", "") for e in entity_group.get("entities", [])]
                
                # Format as: "entity1, entity2, entity3"
                entities_str = ", ".join(entity_texts)
                labels_str = ", ".join(set(entity_labels))  # Unique labels
                
                context = entity_group.get("context", "")
                
                # Make it VERY clear all entities share this citation
                formatted_lines.append(f"\n[{citation_id}] {entities_str}")
                formatted_lines.append(f"    Type: {labels_str}")
                formatted_lines.append(f"    Context: \"{context}\"")

    return "\n".join(formatted_lines)

def validate_citations(summary: Dict[str, Any], citation_map: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that:
    1. All citations used exist in citation_map
    2. No duplicate citations for the same fact (e.g., [1][2])
    
    NEW: Calculates 'Categorical Recall' to see if we are missing specific types of medical data.
    """
    used_citations = set()
    duplicate_citations = []
    citation_pattern = re.compile(r'\[(\d+)\]')
    
    def extract_from_value(value, path=""):
        if isinstance(value, str):
            matches = citation_pattern.findall(value)
            
            # Check for multiple consecutive citations (e.g., [1][2] or [1], [2])
            consecutive_pattern = re.findall(r'(\[\d+\](?:\s*,?\s*\[\d+\])+)', value)
            if consecutive_pattern:
                for dup in consecutive_pattern:
                    duplicate_citations.append({
                        "location": path,
                        "text": value,
                        "duplicate": dup
                    })
            
            used_citations.update(map(str, matches))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                extract_from_value(item, f"{path}[{i}]")
        elif isinstance(value, dict):
            if "citations" in value:
                extract_from_value(value["citations"], f"{path}.citations")
            for k, v in value.items():
                if k != "citations":  # Avoid double-counting
                    extract_from_value(v, f"{path}.{k}")

    extract_from_value(summary)
    
    available_citations = set(map(str, citation_map.keys()))
    invalid_citations = used_citations - available_citations

    # --- NEW CATEGORICAL COVERAGE LOGIC ---
    # 1. Tally available entities by type
    type_stats = {} # { "DISEASE": {"total": 10, "used": 5}, ... }

    for cit_id, data in citation_map.items():
        # Get unique labels in this citation group (e.g. Group [1] might have DISEASE and SEVERITY)
        labels_in_group = set(e.get("label") for e in data.get("entities", []) if e.get("label"))
        
        is_used = str(cit_id) in used_citations
        
        for label in labels_in_group:
            if label not in type_stats:
                type_stats[label] = {"total": 0, "used": 0}
            
            type_stats[label]["total"] += 1
            if is_used:
                type_stats[label]["used"] += 1

    # 2. Calculate percentages
    categorical_coverage = {}
    for label, stats in type_stats.items():
        categorical_coverage[label] = {
            "total": stats["total"],
            "used": stats["used"],
            "percent": round((stats["used"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        }
    
    return {
        "valid": len(invalid_citations) == 0 and len(duplicate_citations) == 0,
        "invalid_citations": list(invalid_citations),
        "duplicate_citations": duplicate_citations,
        "citation_coverage": {
            "total_available": len(available_citations),
            "used": len(used_citations),
            "coverage_percent": round(len(used_citations) / len(available_citations) * 100, 1) if available_citations else 0
        },
        "categorical_coverage": categorical_coverage # <--- NEW METRIC
    }
    

def generate_medical_summary(timeline_with_entities, citation_map: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Format the context-rich entities for the LLM
        entities_text = format_entities_for_prompt(timeline_with_entities)
        
        # Prepare the static parts of the prompt
        schema_str = json.dumps(JSON_SCHEMA, indent=2)
        example_str = json.dumps(EXAMPLE_SUMMARY, indent=2)
        
        # Generate available citation IDs list
        citation_ids_list = ", ".join([f"[{k}]" for k in sorted(citation_map.keys(), key=int)])
        
        print("\n" + "="*80)
        print("FORMATTED ENTITIES FOR LLM:")
        print("="*80)
        print(entities_text[:1000])  # Print first 1000 chars for debugging
        print("="*80 + "\n")
        
        # Run the chain
        result = chain.invoke({
            "entities": entities_text,
            "json_schema": schema_str,
            "example": example_str,
            "citation_ids": citation_ids_list
        })
        
        # --- APPLY SANITIZATION HERE ---
        sanitized_result = _sanitize_summary(result)
        
        # Validation runs on the sanitized result
        validation = validate_citations(sanitized_result, citation_map)
        
        if not validation["valid"]:
            print("\n⚠️  CITATION VALIDATION WARNINGS:")
            # ...existing code...
            if validation["invalid_citations"]:
                print(f"   Invalid IDs used: {validation['invalid_citations']}")
            if validation["duplicate_citations"]:
                print(f"   Duplicate citations found: {len(validation['duplicate_citations'])} instances")
                for dup in validation["duplicate_citations"][:5]:  # Show first 5
                    print(f"      - {dup['duplicate']} in {dup['location']}")
        
        return {
            "summary": sanitized_result, # Return sanitized result
            "citation_map": citation_map,
            "validation": validation
        }
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        raise e