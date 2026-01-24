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

EXAMPLE_SUMMARY = {
    "patient_demographics": {
        "age": "74y",
        "sex": "female"
    },
    "chief_complaint": "Abdominal pain [1]",
    "history_of_present_illness": "74-year-old female with type 2 diabetes mellitus [2] and recent stroke [3] presented with 2 days of abdominal pain [1]",
    "past_medical_history": [
        "Colon cancer diagnosed 2554, treated with hemicolectomy, XRT, chemotherapy [4]",
        "Type II Diabetes Mellitus [2]",
        "Hypertension [5]"
    ],
    "medications": [
        {"name": "Miconazole Nitrate", "dosage": "2% Powder topical BID", "citations": "[6]"},
        {"name": "Heparin Sodium", "dosage": "5,000 unit/mL TID", "citations": "[7]"},
        {"name": "Acetaminophen", "dosage": "160 mg/5 mL Q4-6H PRN", "citations": "[8]"}
    ],
    "procedures": [
        "PICC line insertion [9]",
        "ERCP with sphincterotomy [10]"
    ],
    "diagnostic_findings": [
        "Ultrasound showed pancreatic duct dilation [11]",
        "Edematous gallbladder [11]"
    ],
    "assessment": "Pancreatitis with complications [1][11]",
    "clinical_course": "Patient admitted to ICU [12]. Underwent ERCP with sphincterotomy [10]. Clinical improvement noted [13]"
}

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a medical documentation specialist. Generate a comprehensive medical summary using ONLY the provided entities.

CRITICAL CITATION RULES:
1. ONLY use citation IDs that appear in the input ([1], [2], [3], etc.)
2. Do NOT invent or skip citation numbers
3. Place citations at the end of EACH individual claim
4. For multi-fact sentences, cite each fact separately: "Hypertension [2] and diabetes [5]"
5. Demographics (age, sex) MUST have citations if they appear in entities
6. For medications:
   - Do NOT put citations in "name" or "dosage" text
   - ONLY use the "citations" field: {{"name": "Lisinopril", "citations": "[3]"}}
7. For empty fields: Use [] or omit field. Do NOT write "None noted" or "Not mentioned"
8. Use details from both entity text AND context when relevant
9. List conditions separately unless they share the same citation ID
10. For multi-sentence fields (clinical_course), cite after each sentence

VALIDATION CHECKLIST:
- Every fact has a citation?
- All citation numbers exist in input?
- No made-up information?
- Demographics cited?
- Medications use "citations" field only?

OUTPUT FORMAT:
Generate a valid JSON object matching the example below.

EXAMPLE OUTPUT FORMAT:
{example}

Remember: EVERY fact must have a citation. Use only the citation IDs provided in the input."""),
    ("human", """Input Entities with Citation IDs:

{entities}

Generate the medical summary with proper citations.""")
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
                 # Handle the 'entities' list inside the group
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
        # Debugging: Print the Citation Map
        print("\n--- DEBUG: Citation Map ---")
        print(json.dumps(citation_map, indent=2, default=str)) # default=str to handle non-serializable objects
        print("---------------------------\n")

        entities_text = format_entities_for_prompt(timeline_with_entities)
        
        example_json = json.dumps(EXAMPLE_SUMMARY, indent=2)
        
        result = chain.invoke({
            "entities": entities_text,
            "example": example_json
        })
        
        validation = validate_citations(result, citation_map)
        
        return {
            "summary": result,
            "validation": validation
        }
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        raise e