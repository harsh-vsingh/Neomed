from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from utils.smart_parser import SmartClinicalParser
from services.entity_extract import process_date_chunks
from services.summarizer import generate_medical_summary

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
    summary: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    differential_diagnosis: List[Dict[str, Any]]


@app.post("/")
def home():
    return {"message": "Welcome to the NeoMed Backend API"}


@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: NoteRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content is empty.")
    
    try:
        parsed_result = parser.parse_document(request.text.encode('utf-8'), "input_text.txt")
        
        timeline = parsed_result.get('timeline', [])
        
        if not timeline:
            raise HTTPException(status_code=400, detail="No timeline data extracted from text.")
        
        chunks_for_ner = [
            {"date": episode["date"], "text": episode["content"]}
            for episode in timeline
        ]
        
        timeline_with_entities = process_date_chunks(
            chunks_for_ner,
            context_window=5,
            confidence_threshold=0.5,
            similarity_threshold=0.8
        )
        
        medical_summary = generate_medical_summary(timeline_with_entities)
        
        return AnalysisResponse(
            summary=medical_summary,
            timeline=timeline_with_entities,
            differential_diagnosis=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing text: {str(e)}")


@app.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        parsed_result = parser.parse_document(contents, file.filename)
        
        timeline = parsed_result.get('timeline', [])
        
        if not timeline:
            raise HTTPException(status_code=400, detail="No timeline data extracted from file.")
        
        chunks_for_ner = [
            {"date": episode["date"], "text": episode["content"]}
            for episode in timeline
        ]
        
        timeline_with_entities = process_date_chunks(
            chunks_for_ner,
            context_window=5,
            confidence_threshold=0.5,
            similarity_threshold=0.8
        )
        
        medical_summary = generate_medical_summary(timeline_with_entities)
        
        return AnalysisResponse(
            summary=medical_summary,
            timeline=timeline_with_entities,
            differential_diagnosis=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy"}
    
if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000, reload=True)