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

# Updated Response Model to include warnings
class AnalysisResponse(BaseModel):
    summary: Dict[str, Any]
    timeline: List[Dict[str, Any]]
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
    graph_diagnosis = []

    try:
        # 1. Parse Document / Timeline (Critical)
        try:
            parsed_result = parser.parse_document(request.text.encode('utf-8'), "input_text.txt")
            timeline = parsed_result.get('timeline', [])
            if not timeline:
                 # Fallback if no dates found, treat whole text as one chunk
                 timeline = [{"date": "Unknown Date", "content": request.text}]
        except Exception as e:
            print(f"Parser Error: {e}")
            timeline = [{"date": "Unknown Date", "content": request.text}]

        # 2. NER & Graph Logic (Optional - can fail gracefully)
        detected_symptoms = []
        try:
            full_text_entities = extract_medical_entities(request.text)
            detected_symptoms = list(set([
                e['word'] for e in full_text_entities 
                if e['entity_group'] == 'SIGN_SYMPTOM'
            ]))
            print(f"🔍 Detected Symptoms: {detected_symptoms}")
        except Exception as e:
            print(f"NER Error: {e}")
            warnings.append(f"AI Entity Extraction failed (HuggingFace): {str(e)}")

        # 3. Graph Reasoning
        if detected_symptoms:
            try:
                graph_diagnosis = graph_engine.run_differential_diagnosis(detected_symptoms)
            except Exception as e:
                print(f"Graph Error: {e}")
                warnings.append(f"Graph Database Connection failed (Neo4j): {str(e)}")
        
        # 4. Summarization
        try:
            chunks_for_ner = [
                {"date": episode["date"], "text": episode["content"]}
                for episode in timeline
            ]
            
            # If NER previously failed, this might fail too, so we catch it
            try:
                timeline_with_entities = process_date_chunks(
                    chunks_for_ner,
                    context_window=5,
                    confidence_threshold=0.5,
                    similarity_threshold=0.8
                )
            except:
                # Fallback: just return text without entities
                timeline_with_entities = [{"date": c["date"], "entities": []} for c in chunks_for_ner]
            
            medical_summary = generate_medical_summary(timeline_with_entities)
        except Exception as e:
            print(f"Summarizer Error: {e}")
            warnings.append(f"Summary Generation failed (Gemini): {str(e)}")
            medical_summary = {"error": "Summary unavailable."}
        
        return AnalysisResponse(
            summary=medical_summary,
            timeline=timeline_with_entities,
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
    graph_diagnosis = []

    try:
        contents = await file.read()
        
        # 1. Parsing
        try:
            parsed_result = parser.parse_document(contents, file.filename)
            timeline = parsed_result.get('timeline', [])
            if not timeline:
                raise ValueError("No text content could be extracted from this file.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"File Parsing Failed: {str(e)}")
        
        full_text = " ".join([t['content'] for t in timeline])

        # 2. NER & Graph
        detected_symptoms = []
        try:
            full_text_entities = extract_medical_entities(full_text)
            detected_symptoms = list(set([
                e['word'] for e in full_text_entities 
                if e['entity_group'] == 'SIGN_SYMPTOM'
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
        
        # 3. Summarization
        try:
            chunks_for_ner = [
                {"date": episode["date"], "text": episode["content"]}
                for episode in timeline
            ]
            
            # Safe Chunk Processing
            try:
                timeline_with_entities = process_date_chunks(chunks_for_ner)
            except:
                timeline_with_entities = [{"date": c["date"], "entities": []} for c in chunks_for_ner]

            medical_summary = generate_medical_summary(timeline_with_entities)
        except Exception as e:
            print(f"Summarizer Error: {e}")
            warnings.append(f"Summary generation failed.")
            medical_summary = {"note": "Summary could not be generated."}
        
        return AnalysisResponse(
            summary=medical_summary,
            timeline=timeline_with_entities,
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