from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class GraphAugmenter:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def augment_common_diseases(self):
        print("💉 Injecting common diseases into Knowledge Graph...")
        
        # List of common primary care diseases missing or weak in Hetionet
        # We manually define the Disease -> Symptom edges
        common_knowledge = [
    # Existing ones (keep these)
    {"disease": "Common Cold", "symptoms": ["fever", "cough", "runny nose", "sore throat", "sneezing", "congestion"]},
    {"disease": "Influenza", "symptoms": ["fever", "chills", "muscle ache", "cough", "congestion", "runny nose", "headache", "fatigue"]},
    {"disease": "Acute Bronchitis", "symptoms": ["cough", "mucus", "fatigue", "shortness of breath", "fever", "chest discomfort"]},
    {"disease": "Pneumonia", "symptoms": ["cough", "fever", "chills", "shortness of breath", "chest pain", "nausea"]},
    {"disease": "Gastroenteritis", "symptoms": ["diarrhea", "vomiting", "stomach pain", "fever", "nausea", "headache"]},
    {"disease": "Migraine", "symptoms": ["headache", "nausea", "vomiting", "sensitivity to light"]},
    {"disease": "COVID-19", "symptoms": ["fever", "cough", "fatigue", "loss of taste", "loss of smell", "shortness of breath"]},
    
    # ADD THESE HIGH-PRIORITY CONDITIONS:
    
    # Cardiac
    {"disease": "Acute Coronary Syndrome", "symptoms": ["chest pain", "shortness of breath", "nausea", "diaphoresis", "dizziness", "fatigue"]},
    {"disease": "Heart Failure", "symptoms": ["shortness of breath", "edema", "fatigue", "orthopnea", "weight gain", "cough"]},
    {"disease": "Atrial Fibrillation", "symptoms": ["palpitations", "shortness of breath", "dizziness", "chest discomfort", "fatigue"]},
    
    # Respiratory
    {"disease": "Asthma Exacerbation", "symptoms": ["wheezing", "shortness of breath", "chest tightness", "cough"]},
    {"disease": "COPD Exacerbation", "symptoms": ["shortness of breath", "cough", "wheezing", "chest tightness", "fatigue"]},
    {"disease": "Pulmonary Embolism", "symptoms": ["shortness of breath", "chest pain", "cough", "tachycardia", "dizziness"]},
    
    # GI
    {"disease": "Acute Appendicitis", "symptoms": ["abdominal pain", "nausea", "vomiting", "fever", "loss of appetite"]},
    {"disease": "Cholecystitis", "symptoms": ["abdominal pain", "nausea", "vomiting", "fever", "jaundice"]},
    {"disease": "Peptic Ulcer", "symptoms": ["abdominal pain", "nausea", "vomiting", "bloating", "heartburn"]},
    
    # Endocrine
    {"disease": "Diabetic Ketoacidosis", "symptoms": ["nausea", "vomiting", "abdominal pain", "confusion", "polyuria", "polydipsia", "fatigue"]},
    {"disease": "Hypoglycemia", "symptoms": ["confusion", "sweating", "tremor", "palpitations", "dizziness", "weakness"]},
    {"disease": "Hypothyroidism", "symptoms": ["fatigue", "weight gain", "cold intolerance", "constipation", "dry skin"]},
    
    # Infectious
    {"disease": "Urinary Tract Infection", "symptoms": ["dysuria", "fever", "abdominal pain", "urinary frequency", "urgency"]},
    {"disease": "Sepsis", "symptoms": ["fever", "confusion", "hypotension", "tachycardia", "shortness of breath", "chills"]},
    {"disease": "Cellulitis", "symptoms": ["redness", "swelling", "pain", "warmth", "fever"]},
    
    # Neurological
    {"disease": "Stroke", "symptoms": ["confusion", "weakness", "speech difficulty", "facial droop", "vision changes", "dizziness"]},
    {"disease": "Seizure", "symptoms": ["confusion", "loss of consciousness", "muscle jerking", "staring"]},
    {"disease": "Meningitis", "symptoms": ["headache", "fever", "neck stiffness", "confusion", "nausea", "photophobia"]},
    
    # Renal
    {"disease": "Acute Kidney Injury", "symptoms": ["decreased urine output", "edema", "fatigue", "confusion", "nausea"]},
    {"disease": "Nephrolithiasis", "symptoms": ["flank pain", "abdominal pain", "nausea", "vomiting", "hematuria"]},

    {"disease": "Acute Otitis Media", "symptoms": ["ear pain", "hearing loss", "fever", "fussiness", "balance problems"]},
    {"disease": "Acute Sinusitis", "symptoms": ["facial pain", "nasal congestion", "runny nose", "headache", "tooth pain", "loss of smell"]},
    {"disease": "Infectious Mononucleosis", "symptoms": ["fatigue", "fever", "sore throat", "swollen lymph nodes", "loss of appetite"]},
    
    # Psychiatry
    {"disease": "Major Depressive Disorder", "symptoms": ["depressed mood", "loss of interest", "weight changes", "insomnia", "fatigue", "difficulty concentrating"]},
    {"disease": "Generalized Anxiety Disorder", "symptoms": ["excessive worry", "restlessness", "fatigue", "irritability", "muscle tension", "sleep disturbance"]},
    {"disease": "Panic Attack", "symptoms": ["palpitations", "sweating", "trembling", "shortness of breath", "chest pain", "fear of dying"]},
    
    # Musculoskeletal
    {"disease": "Osteoarthritis", "symptoms": ["joint pain", "stiffness", "tenderness", "loss of flexibility", "bone spurs"]},
    {"disease": "Gout", "symptoms": ["severe joint pain", "swelling", "redness", "tenderness", "limited range of motion"]},
    {"disease": "Fibromyalgia", "symptoms": ["widespread pain", "fatigue", "cognitive difficulties", "sleep problems", "headache"]},
    
    # Dermatology
    {"disease": "Shingles", "symptoms": ["pain", "burning", "numbness", "red rash", "blisters", "itching"]},
    {"disease": "Urticaria", "symptoms": ["itching", "red welts", "swelling"]}
]

        with self.driver.session() as session:
            for item in common_knowledge:
                disease = item['disease']
                print(f"   Processing {disease}...")
                
                # 1. Ensure Disease Node exists (merge avoids duplicates)
                session.run("""
                    MERGE (d:Disease {name: $name})
                    ON CREATE SET d.kind = 'Disease', d.source = 'Manual_Augmentation'
                """, name=disease)
                
                # 2. Link Symptoms
                for symptom in item['symptoms']:
                    # Ensure Symptom exists (Hetionet usually has the symptom names, but we make sure)
                    session.run("""
                        MERGE (s:Symptom {name: $name})
                        ON CREATE SET s.kind = 'Symptom'
                    """, name=symptom)
                    
                    # Create Relationship
                    session.run("""
                        MATCH (d:Disease {name: $disease})
                        MATCH (s:Symptom {name: $symptom})
                        MERGE (d)-[:DpS {source: 'Manual_Augmentation'}]->(s)
                    """, disease=disease, symptom=symptom)
                    
        print("\n✅ Booster pack applied! Common diseases are now in the graph.")

if __name__ == "__main__":
    augmenter = GraphAugmenter()
    augmenter.augment_common_diseases()
    augmenter.close()