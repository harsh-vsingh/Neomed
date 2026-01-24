from typing import List, Dict, Any, Tuple
import os
import requests
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

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
client = InferenceClient(model="blaze999/Medical-NER", token=HF_TOKEN)

HF_API_URL = "https://router.huggingface.co/models/blaze999/Medical-NER"

if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in environment variables")

def call_hf_api(text: str) -> List[Dict[str, Any]]:
    try:
        response = client.token_classification(text)
        
        return [
            {
                "entity_group": item.entity_group,
                "score": item.score,
                "word": item.word,
                "start": item.start,
                "end": item.end
            } 
            for item in response
        ]
        
    except Exception as e:
        print(f"⚠️ SDK Failed, retrying manual: {e}")
        API_URL = "https://api-inference.huggingface.co/models/blaze999/Medical-NER"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        r = requests.post(API_URL, headers=headers, json={"inputs": text})
        
        if r.status_code != 200:
             raise Exception(f"HF API Error: {r.status_code} - {r.text}")
        return r.json()

def context_similarity(ctx1: str, ctx2: str) -> float:
    """Calculate Jaccard similarity between two context strings"""
    words1 = set(ctx1.lower().split())
    words2 = set(ctx2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def extract_medical_entities(text: str, context_window: int = 5, 
                            confidence_threshold: float = 0.5, 
                            similarity_threshold: float = 0.8,
                            citation_counter: int = 1) -> Tuple[List[Dict[str, Any]], int]:
    raw_entities = call_hf_api(text)
    
    words = text.split()
    
    char_to_word_idx = {}
    char_pos = 0
    for word_idx, word in enumerate(words):
        for i in range(len(word)):
            char_to_word_idx[char_pos + i] = word_idx
        char_pos += len(word) + 1
    
    entities = []
    
    for ent in raw_entities:
        if ent["entity_group"] not in ALLOWED_LABELS:
            continue
        if ent["score"] < confidence_threshold:
            continue
            
        start_char = ent["start"]
        end_char = ent["end"]
        
        start_word_idx = char_to_word_idx.get(start_char, 0)
        end_word_idx = char_to_word_idx.get(end_char - 1, len(words) - 1)
        
        context_start = max(0, start_word_idx - context_window)
        context_end = min(len(words), end_word_idx + context_window + 1)
        context_words = words[context_start:context_end]
        
        entities.append({
            "text": ent["word"].strip(),
            "label": ent["entity_group"],
            "confidence": float(ent["score"]),
            "context": " ".join(context_words),
            "context_window_start": context_start,
            "context_window_end": context_end - 1,
            "entity_word_start": start_word_idx,
            "entity_word_end": end_word_idx
        })
    
    grouped_entities = []
    used_indices = set()
    
    for i, ent in enumerate(entities):
        if i in used_indices:
            continue
        
        group = {
            "citation_id": citation_counter,
            "entities": [{"text": ent["text"], "label": ent["label"], "confidence": ent["confidence"]}],
            "context": ent["context"],
            "context_window_start": ent["context_window_start"],
            "context_window_end": ent["context_window_end"]
        }
        
        entities_in_group = 1  # Already added the base entity
        
        for j in range(i + 1, len(entities)):
            if j in used_indices:
                continue
            
            # Stop if we already have 3 entities in this group
            if entities_in_group >= 3:
                break
            
            similarity = context_similarity(ent["context"], entities[j]["context"])
            
            if similarity >= similarity_threshold:
                group["entities"].append({
                    "text": entities[j]["text"],
                    "label": entities[j]["label"],
                    "confidence": entities[j]["confidence"]
                })
                used_indices.add(j)
                entities_in_group += 1
        
        grouped_entities.append(group)
        citation_counter += 1
    
    return grouped_entities, citation_counter

def process_date_chunks(chunks: List[Dict[str, str]], 
                       context_window: int = 4,
                       confidence_threshold: float = 0.6,
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