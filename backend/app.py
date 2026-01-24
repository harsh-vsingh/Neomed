from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
# from utils.text_extractor import TextExtractor
from fastapi.middleware.cors import CORSMiddleware
from utils.smart_parser import SmartClinicalParser

app = FastAPI(title="NeoMed Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser = SmartClinicalParser()

class NoteRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AnalysisResponse(BaseModel):
    summary: str
    timeline: List[Dict[str, Any]]
    differential_diagnosis: List[Dict[str, Any]]


@app.post("/")
def home():
    return {"message": "Welcome to the NeoMed Backend API"}


@app.post("/analyze/text" , response_model=AnalysisResponse)
async def analyze_text(request: NoteRequest):
    """
    Docstring for analyze_text
    
    :param request: Description
    :type request: NoteRequest

    Direct Text Endpoint.
    Used for: Typed notes, Copied text, or Dictation results (frontend converts to text).
    """

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content is empty.")
    
    parsed_result = parser.parse_document(request.text.encode('utf-8'), "input_text.txt")
    
    # Placeholder analysis logic (gliner logic)
    return {
        "summary": "Patient presents with chronic conditions (COPD, CHF) worsening over time.", 
        "timeline": parsed_result['timeline'],
        "differential_diagnosis": [
            {"disease": "Acute Decompensated Heart Failure", "confidence": 0.92, "evidence": ["Edema", "Orthopnea", "Elevated BNP"]},
            {"disease": "COPD Exacerbation", "confidence": 0.85, "evidence": ["Wheezing", "History of smoking"]},
            {"disease": "Pneumonia", "confidence": 0.45, "evidence": ["Age", "Dyspnea"]}
        ]
    }

    

@app.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    """
    File Upload Endpoint.
    Used for: PDFs, Images (scans).
    """

    try:
        contents = await file.read()
        # extracted_text = TextExtractor.extract_from_file(contents, file.filename)
        parsed_result = parser.parse_document(contents, file.filename)

        if not parsed_result['timeline']:
            raise HTTPException(status_code=400, detail="could not extract text from the uploaded file.")
        # Placeholder analysis logic (gliner logic)
        return {
            "summary": f"Extracted text from file.",
            "timeline": parsed_result['timeline'],
            "differential_diagnosis": [
                {"disease": "Acute Decompensated Heart Failure", "confidence": 0.92, "evidence": ["Edema", "Orthopnea", "Elevated BNP"]},
                {"disease": "COPD Exacerbation", "confidence": 0.85, "evidence": ["Wheezing", "History of smoking"]},
                {"disease": "Pneumonia", "confidence": 0.45, "evidence": ["Age", "Dyspnea"]}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000, reload=True)