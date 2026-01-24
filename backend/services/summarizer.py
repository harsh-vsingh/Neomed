import os
import json
import re
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY
)

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
    ("system", """You are a specialized Medical Documentation AI. Your task is to transform raw medical entities into a structured JSON summary.

### CRITICAL RULES:
1. **Source Truth**: Use ONLY the information provided in the entities and their context. Do not add outside medical knowledge.
2. **Exactly One Citation**: Every medical fact must have exactly ONE citation (e.g., [1]). 
   - WRONG: "Hypertension [1][2]"
   - RIGHT: "Hypertension [1]"
3. **No Invention**: Use only the Citation IDs provided in the input. Never invent a citation ID like [999].
4. **Citation Placement**: 
   - In lists and strings: Place [N] immediately after the fact.
   - In Medications: Place [N] ONLY in the dedicated "citations" field.
5. **Combined Facts**: If a sentence contains facts from different citations, cite them individually: "Hypertension [4] and Diabetes [5]".
6. **Empty Fields**: If no entities exist for a specific section, return an empty array [] or null. Do NOT write "None" or "Not applicable".
7. **Contextual Detail**: Use the provided 'Context' to add relevant clinical descriptions (e.g., instead of just "Pain", use "Severe radiating chest pain" if the context supports it).

### JSON SCHEMA:
{json_schema}

### EXAMPLE OUTPUT:
{example}"""),
    ("human", """### INPUT ENTITIES WITH CITATION IDs:
{entities}

Generate the medical summary in the required JSON format following all rules strictly.""")
])

output_parser = JsonOutputParser()
chain = prompt_template | llm | output_parser

def format_entities_for_prompt(timeline: List[Dict[str, Any]]) -> str:
    formatted_lines = []
    
    for date_chunk in timeline:
        date = date_chunk["date"]
        formatted_lines.append(f"\nDate: {date}")
        
        for entity_group in date_chunk["entities"]:
             # If entity_group is a list (nested structure), iterate through it
            if isinstance(entity_group, list):
                 pass 
            # If it's a dict (expected GroupedEntity structure from updated format)
            elif isinstance(entity_group, dict):
                 # Handle the 'entities' list inside the groupth 
                 # Note: in updated entity_extract, key is 'citation_id' (single int), not 'citation_ids' list
                 citation_id = entity_group.get("citation_id")
                 citation_str = f" [{citation_id}]" if citation_id else ""
                 
                 # Get entity texts
                 texts = [e.get("text", "") for e in entity_group.get("entities", [])]
                 texts_str = ", ".join(texts)
                 
                 context = entity_group.get("context", "")
                 
                 formatted_lines.append(f"- {texts_str}{citation_str} (Context: {context})")

    return "\n".join(formatted_lines)

def validate_citations(summary: Dict[str, Any], citation_map: Dict[str, Any]) -> Dict[str, Any]:
    used_citations = set()
    citation_pattern = re.compile(r'\[(\d+)\]')
    
    def extract_from_value(value):
        if isinstance(value, str):
            matches = citation_pattern.findall(value)
            used_citations.update(map(str, matches))
        elif isinstance(value, list):
            for item in value:
                extract_from_value(item)
        elif isinstance(value, dict):
             if "citations" in value:
                 extract_from_value(value["citations"])
             for k, v in value.items():
                 extract_from_value(v)

    extract_from_value(summary)
    
    available_citations = set(map(str, citation_map.keys()))
    invalid_citations = used_citations - available_citations
    
    return {
        "valid": len(invalid_citations) == 0,
        "invalid_citations": list(invalid_citations),
        "citation_coverage": {
            "total_available": len(available_citations),
            "used": len(used_citations),
            "coverage_percent": round(len(used_citations) / len(available_citations) * 100, 1) if available_citations else 0
        }
    }
def generate_medical_summary(timeline_with_entities, citation_map: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Format the context-rich entities for the LLM
        entities_text = format_entities_for_prompt(timeline_with_entities)
        
        # Prepare the static parts of the prompt
        schema_str = json.dumps(JSON_SCHEMA, indent=2)
        example_str = json.dumps(EXAMPLE_SUMMARY, indent=2)
        
        # Run the chain
        result = chain.invoke({
            "entities": entities_text,
            "json_schema": schema_str,
            "example": example_str
        })
        
        validation = validate_citations(result, citation_map)
        
        return {
            "summary": result,
            "validation": validation
        }
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        raise e