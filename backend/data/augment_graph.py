from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class GraphAugmenter:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def augment_common_diseases(self):
        print("💉 Injecting common diseases into Knowledge Graph...")
        
        # List of common primary care diseases missing or weak in Hetionet
        # We manually define the Disease -> Symptom edges
        common_knowledge = [
            {
                "disease": "Common Cold",
                "symptoms": ["fever", "cough", "runny nose", "sore throat", "sneezing", "congestion"]
            },
            {
                "disease": "Influenza",
                "symptoms": ["fever", "chills", "muscle ache", "cough", "congestion", "runny nose", "headache", "fatigue"]
            },
            {
                "disease": "Acute Bronchitis",
                "symptoms": ["cough", "mucus", "fatigue", "shortness of breath", "fever", "chest discomfort"]
            },
            {
                "disease": "Pneumonia",
                "symptoms": ["cough", "fever", "chills", "shortness of breath", "chest pain", "nausea"]
            },
            {
                "disease": "Gastroenteritis",
                "symptoms": ["diarrhea", "vomiting", "stomach pain", "fever", "nausea", "headache"]
            },
            {
                "disease": "Migraine",
                "symptoms": ["headache", "nausea", "vomiting", "sensitivity to light"]
            },
            {
                "disease": "COVID-19",
                "symptoms": ["fever", "cough", "fatigue", "loss of taste", "loss of smell", "shortness of breath"]
            }
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