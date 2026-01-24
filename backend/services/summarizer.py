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
    "type": "object",
    "properties": {
        "patient_demographics": {
            "type": "object",
            "properties": {
                "age": {"type": "string", "description": "Age with citation [N]"},
                "sex": {"type": "string", "description": "Sex with citation [N]"}
            }
        },
        "chief_complaint": {"type": "string", "description": "Primary complaint with citation [N]"},
        "history_of_present_illness": {"type": "string", "description": "HPI narrative with citations after each sentence"},
        "past_medical_history": {
            "type": "array",
            "items": {"type": "string", "description": "Each condition with citation [N]"}
        },
        "medications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "dosage": {"type": "string"},
                    "citations": {"type": "string", "pattern": "^\\[\\d+\\]$"}
                },
                "required": ["name", "dosage", "citations"]
            }
        },
        "allergies": {
            "type": "array",
            "items": {"type": "string", "description": "Each allergy with citation [N]"}
        },
        "family_history": {
            "type": "array",
            "items": {"type": "string", "description": "Each condition with citation [N]"}
        },
        "social_history": {"type": "string", "description": "Social habits with citations [N]"},
        "procedures": {
            "type": "array",
            "items": {"type": "string", "description": "Each procedure with citation [N]"}
        },
        "diagnostic_findings": {
            "type": "array",
            "items": {"type": "string", "description": "Each finding with citation [N]"}
        },
        "physical_examination": {"type": "string", "description": "Physical exam findings with citations [N]"},
        "assessment": {"type": "string", "description": "Clinical diagnosis with citation [N]"},
        "plan": {"type": "string", "description": "Treatment plan with citations [N]"},
        "clinical_course": {"type": "string", "description": "Hospital course with citations after each sentence"}
    }
}

EXAMPLE_SUMMARY = {
    "patient_demographics": {
        "age": "74 years [1]",
        "sex": "female [1]"
    },
    "chief_complaint": "Abdominal pain [2]",
    "history_of_present_illness": "74-year-old female [1] with type 2 diabetes mellitus [3] presented with 2 days of severe abdominal pain [2]. Pain is constant and radiating to back [2].",
    "past_medical_history": [
        "Type 2 diabetes mellitus [3]",
        "Hypertension [4]",
        "Hyperlipidemia [5]"
    ],
    "medications": [
        {"name": "Lisinopril", "dosage": "10mg daily", "citations": "[6]"},
        {"name": "Metformin", "dosage": "500mg twice daily", "citations": "[7]"}
    ],
    "allergies": [
        "Penicillin [8]"
    ],
    "family_history": [
        "Father with coronary artery disease [9]"
    ],
    "social_history": "Former smoker, quit 10 years ago [10]. Denies alcohol use [10].",
    "procedures": [
        "ERCP with sphincterotomy [11]"
    ],
    "diagnostic_findings": [
        "Ultrasound showed pancreatic duct dilation [12]",
        "Elevated lipase 450 U/L [13]"
    ],
    "physical_examination": "Abdomen tender in epigastric region [14]. No rebound tenderness [14].",
    "assessment": "Acute pancreatitis [15]",
    "plan": "NPO, IV hydration, pain management [16]. Repeat lipase in 24 hours [16].",
    "clinical_course": "Patient admitted to ICU [17]. Underwent ERCP with sphincterotomy [11]. Clinical improvement noted on day 3 [18]."
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
- Only include fields that have entities in the input

You MUST follow this JSON schema exactly:
{json_schema}

OUTPUT FORMAT EXAMPLE:
{example}

Remember: Every fact needs EXACTLY ONE citation. Follow the JSON schema structure."""),
    ("human", """Input Entities with Citation IDs:

{entities}

Generate the medical summary with proper citations following the JSON schema.""")
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
        schema_json = json.dumps(JSON_SCHEMA, indent=2)

        result = chain.invoke({
            "entities": entities_text,
            "example": example_json,
            "json_schema": schema_json
        })
        
        validation = validate_citations(result, citation_map)
        
        return {
            "summary": result,
            "validation": validation
        }
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        raise e