from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class KnowledgeGraphService:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query_symptoms_for_disease(self, disease_name):
        """Find symptoms associated with a disease"""
        query = """
        MATCH (d:Disease)-[:DpS]->(s:Symptom)
        WHERE toLower(d.name) CONTAINS toLower($name)
        RETURN d.name as disease, collect(s.name) as symptoms
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, name=disease_name)
            return [record.data() for record in result]

    def find_potential_diseases(self, symptoms: list):
        """
        Given a list of symptoms, find diseases that match.
        Returns diseases ranked by:
        1. Number of matching symptoms (primary)
        2. Whether it's a common disease (boosted)
        3. Match percentage relative to total disease symptoms (specifies fit)
        """
        query = """
        MATCH (d:Disease)-[r:DpS]->(s:Symptom)
        WHERE toLower(s.name) IN $symptoms
        
        // Calculate raw match count and grab the edge source
        WITH d, count(s) as match_count, collect(s.name) as matched_symptoms, collect(r.source) as sources
        
        // Check if any relationship was manually added (meaning it's a common disease we added)
        WITH d, match_count, matched_symptoms,
             CASE WHEN 'Manual_Augmentation' IN sources THEN 10 ELSE 0 END as boost_score
             
        // Return score = (match_count * 2) + boost_score
        // This ensures a 2-symptom common flu (4 + 10 = 14) beats a 4-symptom rare cancer (8 + 0 = 8)
        RETURN d.name as disease, match_count, matched_symptoms, (match_count * 2 + boost_score) as final_score
        ORDER BY final_score DESC
        LIMIT 10
        """
        # Lowercase symptoms for matching
        clean_symptoms = [s.lower() for s in symptoms]
        
        with self.driver.session() as session:
            result = session.run(query, symptoms=clean_symptoms)
            return [record.data() for record in result]
            
    def get_treatments(self, disease_name):
        """Find compounds (drugs) that treat a disease"""
        query = """
        MATCH (c:Compound)-[:CtD]->(d:Disease)
        WHERE toLower(d.name) CONTAINS toLower($name)
        RETURN d.name as disease, collect(c.name) as treatments
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, name=disease_name)
            return [record.data() for record in result]

# Test it out
if __name__ == "__main__":
    kg = KnowledgeGraphService()
    
    # Test 1: Reverse lookup
    print("\n🔍 Testing Symptom Lookup...")
    symptoms = ["fever", "headache", "shortness of breath"]
    results = kg.find_potential_diseases(symptoms)
    for r in results:
        print(f"Disease: {r['disease']} (Matches: {r['match_count']})")
        
    kg.close()