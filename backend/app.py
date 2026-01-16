from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uvicorn
from utils.text_extractor import TextExtractor
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NeoMed Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoteRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AnalysisResponse(BaseModel):
    summary:str
    original_length:int
    source_type:str


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
    
    # Placeholder analysis logic (gliner logic)
    response = AnalysisResponse(
        summary=f"Received text with {len(request.text)} characters.",
        original_length=len(request.text),
        source_type="direct_text"
    )

    return response

@app.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    """
    File Upload Endpoint.
    Used for: PDFs, Images (scans).
    """

    try:
        contents = await file.read()
        extracted_text = TextExtractor.extract_from_file(contents, file.filename)

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="could not extract text from the uploaded file.")
        # Placeholder analysis logic (gliner logic)
        response = AnalysisResponse(
            summary=f"Extracted text with {len(extracted_text)} characters from file.",
            original_length=len(extracted_text),
            source_type="file_upload"
        )   
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000, reload=True)