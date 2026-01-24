from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from utils.smart_parser import SmartClinicalParser
from services.entity_extract import process_date_chunks, extract_medical_entities
from services.summarizer import generate_medical_summary
from services.kq_query import ClinicalGraphEngine
import traceback

graph_engine = ClinicalGraphEngine()

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
    citation_map: Dict[str, Any]
    validation: Dict[str, Any]
    differential_diagnosis: List[Dict[str, Any]]
    warnings: Optional[List[str]] = [] 

@app.post("/")
def home():
    return {"message": "Welcome to the NeoMed Backend API"}

@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: NoteRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content is empty.")
    
    warnings = []
    medical_summary = {}
    timeline_with_entities = []
    citation_map = {}
    validation = {}
    graph_diagnosis = []

    try:
        try:
            parsed_result = parser.parse_document(request.text.encode('utf-8'), "input_text.txt")
            timeline = parsed_result.get('timeline', [])
            if not timeline:
                 timeline = [{"date": "Unknown Date", "content": request.text}]
        except Exception as e:
            print(f"Parser Error: {e}")
            timeline = [{"date": "Unknown Date", "content": request.text}]

        detected_symptoms = []
        try:
            full_text_entities, _ = extract_medical_entities(request.text)
            detected_symptoms = list(set([
                e['text'] for group in full_text_entities for e in group['entities']
                if e['label'] == 'SIGN_SYMPTOM'
            ]))
            print(f"🔍 Detected Symptoms: {detected_symptoms}")
        except Exception as e:
            print(f"NER Error: {e}")
            warnings.append(f"AI Entity Extraction failed (HuggingFace): {str(e)}")

        if detected_symptoms:
            try:
                graph_diagnosis = graph_engine.run_differential_diagnosis(detected_symptoms)
            except Exception as e:
                print(f"Graph Error: {e}")
                warnings.append(f"Graph Database Connection failed (Neo4j): {str(e)}")
        
        try:
            chunks_for_ner = [
                {"date": episode["date"], "text": episode["content"]}
                for episode in timeline
            ]
            
            try:
                timeline_with_entities, citation_map = process_date_chunks(
                    chunks_for_ner,
                    context_window=5,
                    confidence_threshold=0.5,
                    similarity_threshold=0.8
                )
            except Exception as e:
                print(f"Entity processing error: {e}")
                timeline_with_entities = [{"date": c["date"], "entities": []} for c in chunks_for_ner]
                citation_map = {}
                warnings.append("Entity extraction failed for timeline chunks")
            
            if timeline_with_entities and citation_map:
                try:
                    summary_result = generate_medical_summary(timeline_with_entities, citation_map)
                    medical_summary = summary_result["summary"]
                    validation = summary_result["validation"]
                except Exception as e:
                    print(f"Summarizer Error: {e}")
                    warnings.append(f"Summary Generation failed (Gemini): {str(e)}")
                    medical_summary = {"error": "Summary unavailable."}
                    validation = {"valid": False, "citation_coverage": {"coverage_percent": 0}}
            else:
                medical_summary = {"error": "Insufficient data for summary"}
                validation = {"valid": False, "citation_coverage": {"coverage_percent": 0}}
                
        except Exception as e:
            print(f"Summarizer Pipeline Error: {e}")
            warnings.append(f"Summary Generation failed: {str(e)}")
            medical_summary = {"error": "Summary unavailable."}
            validation = {"valid": False, "citation_coverage": {"coverage_percent": 0}}
        
        return AnalysisResponse(
            summary=medical_summary,
            timeline=timeline_with_entities,
            citation_map=citation_map,
            validation=validation,
            differential_diagnosis=graph_diagnosis,
            warnings=warnings
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Critical Server Error: {str(e)}")


@app.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    warnings = []
    medical_summary = {}
    timeline_with_entities = []
    citation_map = {}
    validation = {}
    graph_diagnosis = []

    try:
        contents = await file.read()
        
        try:
            parsed_result = parser.parse_document(contents, file.filename)
            timeline = parsed_result.get('timeline', [])
            if not timeline:
                raise ValueError("No text content could be extracted from this file.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"File Parsing Failed: {str(e)}")
        
        full_text = " ".join([t['content'] for t in timeline])

        detected_symptoms = []
        try:
            full_text_entities, _ = extract_medical_entities(full_text)
            detected_symptoms = list(set([
                e['text'] for group in full_text_entities for e in group['entities']
                if e['label'] == 'SIGN_SYMPTOM'
            ]))
        except Exception as e:
            print(f"NER Error: {e}")
            warnings.append("Medical Entity Extraction is unavailable.")

        if detected_symptoms:
            try:
                graph_diagnosis = graph_engine.run_differential_diagnosis(detected_symptoms)
            except Exception as e:
                 print(f"Graph Error: {e}")
                 warnings.append("Differential Diagnosis Graph is offline.")
        
        try:
            chunks_for_ner = [
                {"date": episode["date"], "text": episode["content"]}
                for episode in timeline
            ]
            
            try:
                timeline_with_entities, citation_map = process_date_chunks(
                    chunks_for_ner,
                    context_window=5,
                    confidence_threshold=0.5,
                    similarity_threshold=0.8
                )
            except Exception as e:
                print(f"Entity processing error: {e}")
                timeline_with_entities = [{"date": c["date"], "entities": []} for c in chunks_for_ner]
                citation_map = {}
                warnings.append("Entity extraction failed for timeline chunks")

            if timeline_with_entities and citation_map:
                try:
                    summary_result = generate_medical_summary(timeline_with_entities, citation_map)
                    medical_summary = summary_result["summary"]
                    validation = summary_result["validation"]
                except Exception as e:
                    print(f"Summarizer Error: {e}")
                    warnings.append(f"Summary generation failed.")
                    medical_summary = {"note": "Summary could not be generated."}
                    validation = {"valid": False, "citation_coverage": {"coverage_percent": 0}}
            else:
                medical_summary = {"error": "Insufficient data for summary"}
                validation = {"valid": False, "citation_coverage": {"coverage_percent": 0}}
                
        except Exception as e:
            print(f"Summarizer Pipeline Error: {e}")
            warnings.append(f"Summary generation failed.")
            medical_summary = {"note": "Summary could not be generated."}
            validation = {"valid": False, "citation_coverage": {"coverage_percent": 0}}
        
        return AnalysisResponse(
            summary=medical_summary,
            timeline=timeline_with_entities,
            citation_map=citation_map,
            validation=validation,
            differential_diagnosis=graph_diagnosis,
            warnings=warnings
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy"}
    
if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000, reload=True)