from typing import List, Dict, Any
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
    # 2. Use the client instead of manual requests
    try:
        # token_classification is the task for NER
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
    words1 = set(ctx1.lower().split())
    words2 = set(ctx2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def extract_medical_entities(text: str, context_window: int = 5, 
                            confidence_threshold: float = 0.5, 
                            similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
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
            "context": " ".join(context_words)
        })
    
    grouped_entities = []
    used_indices = set()
    
    for i, ent in enumerate(entities):
        if i in used_indices:
            continue
        
        group = {
            "entities": [{"text": ent["text"], "label": ent["label"], "confidence": ent["confidence"]}],
            "context": ent["context"]
        }
        
        for j in range(i + 1, len(entities)):
            if j in used_indices:
                continue
            
            similarity = context_similarity(ent["context"], entities[j]["context"])
            
            if similarity >= similarity_threshold:
                group["entities"].append({
                    "text": entities[j]["text"],
                    "label": entities[j]["label"],
                    "confidence": entities[j]["confidence"]
                })
                used_indices.add(j)
        
        grouped_entities.append(group)
    
    return grouped_entities

def process_date_chunks(chunks: List[Dict[str, str]], 
                       context_window: int = 5,
                       confidence_threshold: float = 0.5,
                       similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
    results = []
    
    for chunk in chunks:
        date = chunk.get("date", "N/A")
        text = chunk.get("text", "")
        
        if not text.strip():
            continue
        
        entities = extract_medical_entities(
            text,
            context_window,
            confidence_threshold,
            similarity_threshold
        )
        
        results.append({
            "date": date,
            "entities": entities
        })
    
    return results