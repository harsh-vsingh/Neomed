import os
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

MEDICAL_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "patient_demographics": {
            "type": "object",
            "properties": {
                "age": {"type": "string"},
                "sex": {"type": "string"}
            }
        },
        "chief_complaint": {"type": "string"},
        "history_of_present_illness": {"type": "string"},
        "past_medical_history": {
            "type": "array",
            "items": {"type": "string"}
        },
        "medications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "dosage": {"type": "string"}
                }
            }
        },
        "procedures": {
            "type": "array",
            "items": {"type": "string"}
        },
        "diagnostic_findings": {
            "type": "array",
            "items": {"type": "string"}
        },
        "assessment": {"type": "string"},
        "clinical_course": {"type": "string"}
    },
    "required": ["chief_complaint", "assessment"]
}

EXAMPLE_SUMMARIES = [
    {
        "patient_demographics": {
            "age": "74y",
            "sex": "female"
        },
        "chief_complaint": "Abdominal pain",
        "history_of_present_illness": "74-year-old female with type 2 diabetes mellitus and recent stroke presented with 2 days of abdominal pain.",
        "past_medical_history": [
            "Colon cancer (diagnosed 2554, treated with hemicolectomy, XRT, chemotherapy)",
            "Type II Diabetes Mellitus",
            "Hypertension"
        ],
        "medications": [
            {"name": "Miconazole Nitrate", "dosage": "2% Powder topical BID"},
            {"name": "Heparin Sodium", "dosage": "5,000 unit/mL TID"},
            {"name": "Acetaminophen", "dosage": "160 mg/5 mL Q4-6H PRN"}
        ],
        "procedures": [
            "PICC line insertion",
            "ERCP with sphincterotomy"
        ],
        "diagnostic_findings": [
            "Ultrasound showed pancreatic duct dilation",
            "Edematous gallbladder"
        ],
        "assessment": "Pancreatitis with complications",
        "clinical_course": "Patient admitted to ICU. Underwent ERCP with sphincterotomy. Clinical improvement noted."
    },
    {
        "patient_demographics": {
            "age": "62y",
            "sex": "male"
        },
        "chief_complaint": "Chest pain",
        "history_of_present_illness": "62-year-old male with history of coronary artery disease presented with acute chest pain radiating to left arm.",
        "past_medical_history": [
            "Coronary artery disease",
            "Hyperlipidemia",
            "Former smoker"
        ],
        "medications": [
            {"name": "Aspirin", "dosage": "81mg daily"},
            {"name": "Atorvastatin", "dosage": "40mg daily"}
        ],
        "procedures": [
            "Cardiac catheterization"
        ],
        "diagnostic_findings": [
            "EKG showed ST elevation in leads II, III, aVF",
            "Troponin elevated at 2.5"
        ],
        "assessment": "Acute inferior wall myocardial infarction",
        "clinical_course": "Patient underwent emergent cardiac catheterization with stent placement to RCA. Post-procedure course uncomplicated."
    }
]

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.2,
    google_api_key=GEMINI_API_KEY
)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a medical documentation specialist. Generate a comprehensive medical summary based ONLY on the extracted entities provided.

STRICT RULES:
1. Use ONLY facts present in the extracted entities
2. Do NOT add information not in the source
3. Do NOT make assumptions or inferences
4. Output MUST follow the exact JSON schema provided
5. If information is missing, omit that field or use empty array
     6. Example summaries are provided for format reference ONLY

JSON Schema:
{schema}

Example Summaries (for format reference only):
{examples}"""),
    ("human", """Extracted Entities (YOUR ONLY SOURCE OF FACTS):
{entities}

Generate a medical summary in the exact JSON format specified. Remember: ONLY use information from the extracted entities above.

Output valid JSON only.""")
])

output_parser = JsonOutputParser()

chain = prompt_template | llm | output_parser

def generate_medical_summary(timeline_with_entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    entities_text = json.dumps(timeline_with_entities, indent=2)
    examples_text = json.dumps(EXAMPLE_SUMMARIES, indent=2)
    schema_text = json.dumps(MEDICAL_SUMMARY_SCHEMA, indent=2)
    
    result = chain.invoke({
        "schema": schema_text,
        "examples": examples_text,
        "entities": entities_text
    })
    
    return result