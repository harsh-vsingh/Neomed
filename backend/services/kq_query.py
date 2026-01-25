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
        Advanced Bayesian-style Scoring System:
        1. Symptom Specificity (IDF): Rare symptoms weigh significantly more than common ones.
           - Matches 'Chest Pain' >> Matches 'Fatigue'
        2. Match Quality: Exact string matches scored higher than partial/fuzzy matches.
        3. Disease Coverage: How much of the disease's profile is explained by inputs?
        4. Manual Boost: Preserves manual augmentation priority.
        """
        query = """
        // 1. Find matched symptoms and calculate their Global Frequency (Rarity)
        UNWIND $symptoms AS input_symptom
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower(input_symptom)
        
        // Calculate Specificity: Count how many diseases trigger this symptom total
        // We use this to down-weight generic symptoms like 'Fatigue'
        MATCH (s)<-[:DpS]-(any_d:Disease)
        WITH s, input_symptom, count(any_d) as global_freq
        
        // 2. Calculate Per-Symptom Score
        WITH s, 
             // A. Match Quality: Exact match gets 100% weight, Partial gets 50%
             CASE 
                WHEN toLower(s.name) = toLower(input_symptom) THEN 1.0 
                ELSE 0.5 
             END as match_quality,
             
             // B. Rarity Weight (Inverse Log Frequency)
             // Rare symptoms (low freq) get high scores. Common ones get low scores.
             // Adding +5 to log denominator prevents division by zero and smooths extreme values
             1.0 / log10(global_freq + 5) as rarity_weight
             
        // 3. Traverse to Candidate Diseases
        MATCH path = (d:Disease)-[r:DpS]->(s)
        
        // 4. Aggregate Scores per Disease
        WITH d, 
             sum(match_quality * rarity_weight) as weighted_symptom_score,
             count(distinct s) as matched_count,
             collect(distinct s.name) as matched_symptoms,
             collect(distinct {
                symptom: s.name,
                weight: round(rarity_weight * 100) / 100
             }) as symptom_breakdown,
             collect(path) as paths, 
             collect(r.source) as sources
             
        // 5. Get Disease Context (Total Dictionary Definitions)
        MATCH (d)-[:DpS]->(all_symptoms:Symptom)
        WITH d, weighted_symptom_score, matched_count, matched_symptoms, symptom_breakdown, paths, sources, 
             count(distinct all_symptoms) as total_disease_symptoms

        // 6. Final Scoring Formula
        WITH d, matched_count, matched_symptoms, total_disease_symptoms, paths, symptom_breakdown,
             
             // Normalize the specificty score (heuristic multiplier to bring it to ~50-60 range)
             (weighted_symptom_score * 25) as specificity_score,
             
             // Coverage Bonus: (Matches / Total Disease Symptoms)
             // Punishes diseases that have 100 symptoms if you only matched 2 generic ones
             (toFloat(matched_count) / toFloat(total_disease_symptoms + 1) * 20) as coverage_bonus,
             
             // Manual Boost for Common Conditions
             CASE WHEN any(x IN sources WHERE x = 'Manual_Augmentation') THEN 15 ELSE 0 END as manual_boost

        WITH d, matched_count, matched_symptoms, total_disease_symptoms, paths,
             round(specificity_score + coverage_bonus + manual_boost) as final_score

        RETURN d.name as disease,
               matched_count as matches, 
               matched_symptoms,
               total_disease_symptoms,
               CASE WHEN final_score > 100 THEN 100 ELSE final_score END as confidence_score,
               [p in paths | {
                    start_node: nodes(p)[0].name, 
                    relationship: type(relationships(p)[0]),
                    end_node: nodes(p)[1].name,
                    source_db: relationships(p)[0].source 
               }] as trace_chain
        
        ORDER BY confidence_score DESC, matched_count DESC
        LIMIT 5
        """
        
        # Clean inputs
        clean_symptoms = [s.strip().lower() for s in symptoms if len(s) > 2]
        
        with self.driver.session() as session:
            result = session.run(query, symptoms=clean_symptoms)
            return [record.data() for record in result]