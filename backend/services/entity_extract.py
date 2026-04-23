from typing import List, Dict, Any, Tuple
import os
import requests
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

ALLOWED_LABELS = {
    "DISEASE_DISORDER",
    "SIGN_SYMPTOM", 
    "MEDICATION",
    "THERAPEUTIC_PROCEDURE",
    "DIAGNOSTIC_PROCEDURE",
    "BIOLOGICAL_STRUCTURE",
    "DOSAGE",
    "LAB_VALUE",
    "AGE",
    "SEX",
    "DURATION"
}

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in environment variables. Please check your .env file.")

# Using a widely available medical NER model
client = InferenceClient(model="blaze999/Medical-NER", token=HF_TOKEN)

def call_hf_api(text: str) -> List[Dict[str, Any]]:
    try:
        response = client.token_classification(text)
        # Ensure sorting by start position for linear processing
        sorted_response = sorted(response, key=lambda x: x.start)
        
        return [
            {
                "entity_group": item.entity_group,
                "score": item.score,
                "word": item.word,
                "start": item.start,
                "end": item.end
            } 
            for item in sorted_response
        ]
        
    except Exception as e:
        print(f"⚠️ SDK Failed, retrying manual: {e}")
        API_URL = "https://api-inference.huggingface.co/models/blaze999/Medical-NER"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        r = requests.post(API_URL, headers=headers, json={"inputs": text})
        
        if r.status_code != 200:
            print(f"❌ HF API Error: {r.status_code} - {r.text}")
            return []
        
        # Normalize manual response to match SDK format
        raw_response = r.json()
        if isinstance(raw_response, list):
            # Sort manually if coming from raw API
            sorted_raw = sorted(raw_response, key=lambda x: x.get("start", 0))
            return [
                {
                    "entity_group": item.get("entity_group", ""),
                    "score": item.get("score", 0.0),
                    "word": item.get("word", ""),
                    "start": item.get("start", 0),
                    "end": item.get("end", 0)
                }
                for item in sorted_raw
            ]
        return []

def context_similarity(ctx1: str, ctx2: str) -> float:
    """Calculate Jaccard similarity between two context strings"""
    words1 = set(ctx1.lower().split())
    words2 = set(ctx2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def extract_medical_entities(text: str, context_window: int = 8, 
                            confidence_threshold: float = 0.65, 
                            similarity_threshold: float = 0.8,
                            citation_counter: int = 1) -> Tuple[List[Dict[str, Any]], int]:
    
    # 1. Get Raw Entities
    raw_entities = call_hf_api(text)
    
    # 2. Map words for context extraction
    words = text.split()
    word_positions = []
    char_pos = 0
    
    for word_idx, word in enumerate(words):
        word_start = text.find(word, char_pos)
        if word_start == -1: word_start = char_pos
        word_end = word_start + len(word)
        word_positions.append({"start": word_start, "end": word_end, "index": word_idx})
        char_pos = word_end
    
    def get_word_index(char_idx: int) -> int:
        if char_idx < 0: return 0
        if char_idx >= len(text): return len(words) - 1
        for wp in word_positions:
            if wp["start"] <= char_idx < wp["end"]: return wp["index"]
        # Fallback closest
        return min(range(len(word_positions)), 
                  key=lambda i: min(abs(char_idx - word_positions[i]["start"]), 
                                  abs(char_idx - word_positions[i]["end"])))

    # 3. Enrich entities with context
    enriched_entities = []
    for ent in raw_entities:
        if ent["entity_group"] not in ALLOWED_LABELS: continue
        if ent["score"] < confidence_threshold: continue
        
        start_idx = get_word_index(ent["start"])
        end_idx = get_word_index(ent["end"] - 1)
        
        c_start = max(0, start_idx - context_window)
        c_end = min(len(words), end_idx + context_window + 1)
        context_text = " ".join(words[c_start:c_end]).strip()
        
        if len(context_text) < 3: continue
        
        enriched_entities.append({
            "text": ent["word"].strip(),
            "label": ent["entity_group"],
            "confidence": float(ent["score"]),
            "start": ent["start"],
            "end": ent["end"],
            "context": context_text,
            "c_start": c_start,
            "c_end": c_end
        })

    # 4. SINGLE STAGE GROUPING (Greedy Clustering)
    # Similar to NER2.ipynb: iterates linearly and merges into existing groups
    grouped_results = []
    
    for ent in enriched_entities:
        merged = False
        
        # Try to find a matching group
        for group in grouped_results:
            # CONSTRAINT: No more than 5 entities per group
            if len(group["entities"]) >= 5:
                continue
            
            # Check 1: Physical Adjacency
            # Compare with the LAST entity added to this specific group
            last_ent = group["__last_ent"] # Internal helper
            gap = ent["start"] - last_ent["end"]
            
            # Adjacent if within 10 chars (e.g., "Heart" + "Failure")
            is_adjacent = 0 <= gap <= 10
            
            # Check 2: Context Similarity (for non-adjacent mentions)
            # Compare with the group's definition (representative context)
            sim = context_similarity(ent["context"], group["context"])
            is_similar = sim >= similarity_threshold
            
            if is_adjacent or is_similar:
                group["entities"].append({
                    "text": ent["text"],
                    "label": ent["label"],
                    "confidence": ent["confidence"]
                })
                # Update last entity tracker for adjacency checks
                group["__last_ent"] = ent 
                merged = True
                break
        
        if not merged:
            # Start a new group
            new_group = {
                "citation_id": citation_counter,
                "context": ent["context"],
                "context_window_start": ent["c_start"],
                "context_window_end": ent["c_end"],
                "entities": [{
                    "text": ent["text"],
                    "label": ent["label"],
                    "confidence": ent["confidence"]
                }],
                "__last_ent": ent  # Helper for adjacency calc, removed before return
            }
            grouped_results.append(new_group)
            citation_counter += 1
            
    # Cleanup internal helpers
    for g in grouped_results:
        del g["__last_ent"]
        
    return grouped_results, citation_counter

def process_date_chunks(chunks: List[Dict[str, Any]], 
                       context_window: int = 7,
                       confidence_threshold: float = 0.65,
                       similarity_threshold: float = 0.8) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    
    results = []
    citation_map = {}
    citation_counter = 1
    
    for chunk_idx, chunk in enumerate(chunks):
        date = chunk.get("date", "N/A")
        text = chunk.get("text", "")
        
        if not text.strip():
            continue
        
        entities, citation_counter = extract_medical_entities(
            text,
            context_window,
            confidence_threshold,
            similarity_threshold,
            citation_counter
        )
        
        # Build citation map globally across chunks
        for entity_group in entities:
            citation_id = str(entity_group["citation_id"])
            citation_map[citation_id] = {
                "date": date,
                "context": entity_group["context"],
                "context_window_start": entity_group["context_window_start"],
                "context_window_end": entity_group["context_window_end"],
                "entities": entity_group["entities"],
                "source_chunk_index": chunk_idx
            }
        
        results.append({
            "date": date,
            "text": text,
            "entities": entities
        })
    
    return results, citation_map