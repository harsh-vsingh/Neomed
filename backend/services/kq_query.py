from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class ClinicalGraphEngine:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_differential_diagnosis(self, symptoms: list):
        """
        Hybrid Scoring System:
        - Base score from absolute matches (each match = 15 points)
        - Bonus from match percentage (up to +30 points)
        - Common disease boost (+15 points for manual augmentation)
        Maximum possible score: 100
        """
        query = """
        // 1. Find Symptom Nodes (Fuzzy Match Case Insensitive)
        UNWIND $symptoms AS input_symptom
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower(input_symptom)
        
        // 2. Traverse to Disease
        MATCH path = (d:Disease)-[r:DpS]->(s)
        
        // 3. Aggregate Matched Symptoms
        WITH d, count(distinct s) as matched_count, collect(distinct s.name) as matched_symptoms, 
             collect(path) as paths, collect(r.source) as sources
        
        // 4. Get Total Symptom Count for this Disease
        MATCH (d)-[:DpS]->(all_symptoms:Symptom)
        WITH d, matched_count, matched_symptoms, paths, sources, count(distinct all_symptoms) as total_disease_symptoms
        
        // 5. Hybrid Scoring System
        WITH d, matched_count, matched_symptoms, paths, sources, total_disease_symptoms,
             // Base score: 15 points per match (capped at 60)
             CASE 
                WHEN matched_count >= 4 THEN 60
                ELSE matched_count * 15
             END as match_score,
             // Percentage bonus: up to 30 points based on coverage
             toFloat(matched_count) / toFloat(total_disease_symptoms) * 30 as percentage_bonus,
             // Common disease boost: +15 for manually augmented
             CASE WHEN any(x IN sources WHERE x = 'Manual_Augmentation') THEN 15 ELSE 0 END as common_boost
        
        WHERE matched_count >= 1
        
        WITH d, matched_count, matched_symptoms, paths, sources, total_disease_symptoms,
             round(match_score + percentage_bonus + common_boost) as confidence_score
        
        RETURN d.name as disease,
               matched_count as matches, 
               matched_symptoms,
               total_disease_symptoms,
               CASE 
                  WHEN confidence_score > 100 THEN 100
                  ELSE confidence_score
               END as confidence_score,
               [p in paths | {
                    start_node: nodes(p)[0].name, 
                    relationship: type(relationships(p)[0]),
                    end_node: nodes(p)[1].name,
                    source_db: relationships(p)[0].source 
               }] as trace_chain
        // ORDER BY: Prioritize confidence score
        ORDER BY confidence_score DESC, matched_count DESC, total_disease_symptoms ASC
        LIMIT 5
        """
        
        # Clean inputs
        clean_symptoms = [s.strip().lower() for s in symptoms if len(s) > 2]
        
        with self.driver.session() as session:
            result = session.run(query, symptoms=clean_symptoms)
            return [record.data() for record in result]