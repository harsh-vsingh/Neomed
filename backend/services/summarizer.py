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
    model="gemini-1.5-flash",
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
   - ONLY use the "citations" field: {"name": "Lisinopril", "citations": "[3]"}
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
{{
  "patient_demographics": {{"age": "string", "sex": "string"}},
  "chief_complaint": "string with [citation]",
  "history_of_present_illness": "string with [citations]",
  "past_medical_history": ["string with [citation]", ...],
  "medications": [{{"name": "string", "dosage": "string", "citations": "[N]"}}, ...],
  "procedures": ["string with [citation]", ...],
  "diagnostic_findings": ["string with [citation]", ...],
  "assessment": "string with [citations]",
  "clinical_course": "string with [citations]"
}}

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
            citation_id = entity_group["citation_id"]
            entities_text = ", ".join([
                f"{e['text']} ({e['label']})" 
                for e in entity_group["entities"]
            ])
            context = entity_group["context"]
            
            formatted_lines.append(f"[{citation_id}] Entities: {entities_text}")
            formatted_lines.append(f"    Context: {context}")
    
    return "\n".join(formatted_lines)

def extract_citations_from_summary(summary: Dict[str, Any]) -> set:
    citation_pattern = r'\[(\d+)\]'
    all_text = json.dumps(summary)
    citations = re.findall(citation_pattern, all_text)
    return set(citations)

def validate_citations(summary: Dict[str, Any], citation_map: Dict[str, Any]) -> Dict[str, Any]:
    summary_citations = extract_citations_from_summary(summary)
    available_citations = set(citation_map.keys())
    
    invalid_citations = summary_citations - available_citations
    uncited_entities = available_citations - summary_citations
    
    coverage = (len(summary_citations) / len(available_citations) * 100) if available_citations else 0
    
    validation_result = {
        "valid": len(invalid_citations) == 0 and len(uncited_entities) == 0,
        "invalid_citations": list(invalid_citations),
        "uncited_entities": list(uncited_entities),
        "citation_coverage": {
            "total_available": len(available_citations),
            "total_cited": len(summary_citations),
            "coverage_percent": round(coverage, 2)
        }
    }
    
    if invalid_citations:
        print(f"⚠️ Warning: Invalid citations found: {invalid_citations}")
    if uncited_entities:
        print(f"⚠️ Warning: Uncited entities: {uncited_entities}")
    
    return validation_result

def generate_medical_summary(timeline_with_entities: List[Dict[str, Any]], 
                            citation_map: Dict[str, Any]) -> Dict[str, Any]:
    
    entities_formatted = format_entities_for_prompt(timeline_with_entities)
    example_text = json.dumps(EXAMPLE_SUMMARY, indent=2)
    
    try:
        result = chain.invoke({
            "example": example_text,
            "entities": entities_formatted
        })
        
        validation = validate_citations(result, citation_map)
        
        return {
            "summary": result,
            "validation": validation
        }
    
    except Exception as e:
        raise ValueError(f"Error generating summary: {e}")