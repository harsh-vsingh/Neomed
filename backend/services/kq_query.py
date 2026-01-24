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
        Sophisticated Query that:
        1. Matches input symptoms to Graph Nodes (fuzzy match)
        2. Traverses edges (DpS: Disease-presents-Symptom)
        3. Returns the FULL PATH for traceability
        """
        query = """
        // 1. Find Symptom Nodes (Fuzzy Match Case Insensitive)
        UNWIND $symptoms AS input_symptom
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower(input_symptom)
        
        // 2. Traverse to Disease
        MATCH path = (d:Disease)-[r:DpS]->(s)
        
        // 3. Aggregate & Score
        // Score logic: Count(Matched Symptoms) * (Boost if Manual Augmentation)
        WITH d, count(distinct s) as matches, collect(distinct s.name) as matched_symptoms, collect(path) as paths, collect(r.source) as sources
        
        // Boost score for "Augmented" relationships (created by our scripts for common diseases)
        WITH d, matches, matched_symptoms, paths,
             CASE WHEN any(x IN sources WHERE x = 'Manual_Augmentation') THEN 15 ELSE 0 END as boost
        
        WHERE matches >= 1
        
        RETURN d.name as disease,
               matches, 
               matched_symptoms,
               (matches * 5 + boost) as confidence_score,
               // Return sources for explainability
               [p in paths | {
                    start_node: nodes(p)[0].name, 
                    relationship: type(relationships(p)[0]),
                    end_node: nodes(p)[1].name,
                    source_db: relationships(p)[0].source 
               }] as trace_chain
        ORDER BY confidence_score DESC
        LIMIT 5
        """
        
        # Clean inputs
        clean_symptoms = [s.strip().lower() for s in symptoms if len(s) > 2]
        
        with self.driver.session() as session:
            result = session.run(query, symptoms=clean_symptoms)
            return [record.data() for record in result]