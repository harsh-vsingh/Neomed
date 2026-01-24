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
        "age": "74 years [1]",
        "sex": "female [1]"
    },
    "chief_complaint": "Abdominal pain [2]",
    "history_of_present_illness": "74-year-old female [1] with type 2 diabetes mellitus [3] presented with 2 days of abdominal pain [2].",
    "past_medical_history": [
        "Type 2 diabetes mellitus [3]",
        "Hypertension [4]"
    ],
    "medications": [
        {"name": "Lisinopril", "dosage": "10mg daily", "citations": "[5]"},
        {"name": "Metformin", "dosage": "500mg twice daily", "citations": "[6]"}
    ],
    "procedures": [
        "ERCP with sphincterotomy [7]"
    ],
    "diagnostic_findings": [
        "Ultrasound showed pancreatic duct dilation [8]"
    ],
    "assessment": "Acute pancreatitis [9]",
    "clinical_course": "Patient admitted to ICU [10]. Underwent ERCP [7]. Clinical improvement noted [11]."
}

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a medical documentation specialist. Generate a comprehensive medical summary using ONLY the provided entities.

CITATION RULES:
1. Each fact gets EXACTLY ONE citation: "Hypertension [2]"
2. Do NOT use multiple citations for one fact: WRONG → "Pancreatitis [1][11]"
3. Only use citation numbers from the input ([1], [2], [3], etc.)
4. Do NOT invent citation numbers
5. Place citation at the end of each claim or sentence
6. List each condition separately with its own citation:
   - CORRECT: ["Hypertension [2]", "Diabetes [3]"]
   - WRONG: ["Hypertension and diabetes [2][3]"]

MEDICATION RULES:
- One citation per medication (covers both name and dosage)
- Put citation ONLY in "citations" field
- CORRECT: {{"name": "Lisinopril", "dosage": "10mg daily", "citations": "[5]"}}
- WRONG: {{"name": "Lisinopril [5]", "dosage": "10mg daily [5]", "citations": "[5]"}}

GENERAL RULES:
- Cite demographics if present: {{"age": "74y [1]", "sex": "female [1]"}}
- For empty fields use [], do NOT write "None noted"
- Use medical terminology from entities
- Add context details when clinically relevant (e.g., "severe", "radiating")
- Do NOT add interpretations not in source

OUTPUT FORMAT:
{example}

Remember: Every fact needs EXACTLY ONE citation."""),
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