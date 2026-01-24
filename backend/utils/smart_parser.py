import re
import io
import pytesseract
from PIL import Image
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class SmartClinicalParser:
    """
    Advanced parser for clinical documents.
    Handles: Hybrid OCR, Noise Cleaning, and TimeStamp-Aware Chunking.
    """
    
    def parse_document(self, file_content: bytes, filename: str) -> dict:
        """
        Main pipeline: Ingest -> Clean -> Segment.
        Returns a structured JSON-ready dictionary.
        """
        # 1. Hybrid Extraction
        raw_text = self._extract_text(file_content, filename)
        
        # 2. Cleaning
        clean_text = self._clean_noise(raw_text)
        
        # 3. TimeStamp-Aware Segmentation (Smart Chunking)
        # Result is ALWAYS a list of dicts: [{'date': '...', 'content': '...'}]
        episodes = self._segment_by_date(clean_text)
        
        return {
            "metadata": {
                "source": filename,
                "total_chars": len(clean_text),
                "extraction_method": "hybrid_ocr" if len(raw_text) < 50 else "digital_pdf"
            },
            "timeline": episodes  # Renamed 'sections' to 'timeline' for clarity
        }

    def _extract_text(self, content: bytes, filename: str) -> str:
        """Hybrid Strategy: Tries Pypdf first. If result is empty/garbage, uses OCR."""
        filename = filename.lower()
        extracted_text = ""

        # Strategy A: Digital Extraction (PDF)
        if filename.endswith('.pdf'):
            try:
                reader = PdfReader(io.BytesIO(content))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            except Exception as e:
                print(f"⚠️ PDF Digital Read failed: {e}")

        # NEW: Strategy C: Plain Text Files
        elif filename.endswith('.txt'):
            return content.decode('utf-8', errors='ignore')

        # Strategy B: Fallback to OCR if text is suspicious (too short or empty)
        # Only try OCR if it's NOT a text file (text files are already pure text)
        if not filename.endswith('.txt') and len(extracted_text.strip()) < 50:
            if filename.endswith('.pdf'):
                # Note: Requires pdf2image for actual OCR on PDF implementation
                pass 
            elif filename.endswith(('.png', '.jpg', '.jpeg')):
                try:
                    image = Image.open(io.BytesIO(content))
                    extracted_text = pytesseract.image_to_string(image)
                except Exception as e:
                    raise ValueError(f"OCR Failed: {e}")
        
        return extracted_text

    def _clean_noise(self, text: str) -> str:
        """Sanitizes the text stream."""
        text = re.sub(r'-\n', '', text) # Fix hyphenation
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text) # Fix broken lines
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE) # Fix footers
        return text.strip()

    def _segment_by_date(self, text: str) -> list:
        """
        Splits text into chunks based on Date headers.
        Returns list of dicts: [{"date": "12/05/2023", "content": "Patient..."}]
        """
        # Common clinical date patterns
        date_pattern = r'(?:Date of Service|DOS|Date):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{4}-\d{2}-\d{2})|((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})'
        
        matches = list(re.finditer(date_pattern, text, re.IGNORECASE))
        
        # Default recursive splitting if no dates found
        if not matches:
            raw_chunks = self._fallback_chunking(text)
            # Normalize to JSON structure
            return [{"date": "N/A", "content": chunk} for chunk in raw_chunks]

        chunks = []
        start_idx = 0
        
        for i, match in enumerate(matches):
            date_str = match.group(0).strip()
            
            # 1. Capture content BEFORE this date (orphaned context)
            if match.start() > start_idx:
                pre_content = text[start_idx:match.start()].strip()
                if pre_content:
                    chunks.append({"date": "Previous History", "content": pre_content})
            
            # 2. Capture content FOR this date
            start_of_content = match.end()
            # Content goes until the NEXT date match starts (or EOF)
            end_of_content = matches[i+1].start() if i + 1 < len(matches) else len(text)
            
            episode_text = text[start_of_content:end_of_content].strip()
            
            chunks.append({
                "date": date_str,
                "content": episode_text
            })
            
            start_idx = end_of_content
            
        return chunks

    def _fallback_chunking(self, text: str) -> list:
        """Safety Net: Returns simple list of strings."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        return text_splitter.split_text(text)

# Test Block
if __name__ == "__main__":
    import json # For pretty printing
    parser = SmartClinicalParser()
    
    test_note = """
    PATIENT NAME: M. R.
MRN: 77A91
AGE: 65-year-old female

Chief Complaint:
Worsening shortness of breath and bilateral leg swelling

HPI:
The pt is a 65-year-old female with known h/o chronic obstructive pulmonary disease, congestive heart failure, and long-standing diabetes mellitus presenting with progressively worsening dyspnea and lower extremity edema. Pt reports that over the recent period she has noticed increased SOB with minimal exertion, including walking short distances inside her home. She now requires multiple pillows to sleep due to breathlessness when lying flat. There is associated weight gain per pt report and tightness of shoes. She endorses intermittent wheezing and productive cough with whitish sputum but denies fever or chills. Pt also complains of generalized fatigue and reduced appetite. No active CP reported, though she describes a vague chest heaviness at times. No syncope. She states that inhaler use provides partial relief. Medication adherence is inconsistent per pt, especially diuretics due to frequent urination.

--- Page 1 of 3 – Confidential – Printed by Hospital EHR ---

Past Medical History:
COPD with multiple prior exacerbations requiring steroids and nebulization
CHF with reduced ejection fraction per prior records
Type 2 Diabetes Mellitus with variable control
Hypertension
Hyperlipidemia
Chronic kidney disease, stage unclear

Past Surgical History:
Cholecystectomy
Cataract extraction

Medications:
Loop diuretic (pt unsure of dose)
ACE inhibitor
Beta blocker
Long-acting bronchodilator inhaler
Short-acting rescue inhaler PRN
Oral hypoglycemic agents
Insulin at night (pt admits occasional missed doses)

Allergies:
No known drug allergies

Family History:
Mother with h/o heart failure and diabetes
Father deceased due to lung disease
Sibling with coronary artery disease

Social History:
Former smoker with significant pack-year exposure, quit several years ago
No alcohol use
Lives with family, limited mobility
Independent in basic activities but requires assistance during exacerbations

Review of Systems:
General: Fatigue, weight gain, decreased exercise tolerance
Respiratory: SOB, wheezing, cough with sputum
Cardiovascular: Orthopnea, leg swelling, occasional palpitations
Gastrointestinal: No abdominal pain, occasional nausea
Genitourinary: Increased urinary frequency when compliant with diuretics
Endocrine: Polyuria, polydipsia at times
Neurologic: No focal deficits, no dizziness
Skin: Tightness and dryness of lower extremities

--- Page 2 of 3 – Confidential ---

Physical Exam:
General: Elderly female, appears fatigued, sitting upright, mild respiratory distress
Vitals: BP elevated, HR mildly tachycardic, RR increased, O2 saturation borderline on room air
HEENT: No JVD at rest, mucous membranes dry
Lungs: Decreased air entry bilaterally, diffuse wheezes, bibasilar crackles
Cardiac: S1 S2 present, soft systolic murmur, no rubs
Abdomen: Soft, non-tender, mild distension
Extremities: Bilateral pitting edema up to mid-calf, skin shiny
Neurologic: Alert and oriented, no gross deficits

Laboratory Data:
Elevated blood glucose levels
Renal function mildly impaired
BNP elevated
Electrolytes show borderline low potassium

Imaging:
Chest imaging demonstrates pulmonary congestion and hyperinflated lungs consistent with COPD and volume overload

Assessment:
Acute on chronic heart failure exacerbation with volume overload
COPD exacerbation contributing to dyspnea
Poorly controlled diabetes mellitus
Medication non-adherence contributing to symptoms

--- Page 3 of 3 – Printed by EHR System ---

Plan:
Admit for optimization of heart failure management
Initiate IV diuretics with close monitoring of urine output and electrolytes
Resume guideline-directed medical therapy for CHF as tolerated
Bronchodilator therapy with scheduled nebulizations
Systemic steroids for COPD exacerbation with planned taper
Supplemental oxygen to maintain adequate saturation
Strict input/output monitoring and daily weights
Blood glucose monitoring with insulin adjustment
Dietary counseling for low sodium and diabetic diet
Education regarding medication adherence and symptom recognition
Consider cardiology and pulmonology consultation
Discharge planning with close outpatient follow-up once clinically stable
    """
    
    print("\n📝 PROCESSING TEST DOCUMENT...\n")
    

    
    result = parser.parse_document(test_note.encode('utf-8'), "test_file.txt")
    
    # Print JSON Output
    print(json.dumps(result, indent=2))