import json
from neo4j import GraphDatabase
from tqdm import tqdm
import time

class HetionetLoader:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password123"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
    
    def create_indexes(self):
        """Create indexes for faster queries"""
        with self.driver.session() as session:
            print("📇 Creating indexes...")
            # Constraint is better than index for IDs (ensures uniqueness)
            try:
                session.run("CREATE CONSTRAINT FOR (n:Node) REQUIRE n.id IS UNIQUE")
            except Exception:
                pass # Might already exist
                
            indexes = [
                "CREATE INDEX disease_name IF NOT EXISTS FOR (n:Disease) ON (n.name)",
                "CREATE INDEX symptom_name IF NOT EXISTS FOR (n:Symptom) ON (n.name)",
                "CREATE INDEX compound_name IF NOT EXISTS FOR (n:Compound) ON (n.name)", 
            ]
            
            for idx in indexes:
                session.run(idx)
            print("✅ Indexes created")

    def load_nodes(self, filepath="hetionet_nodes_all.json"):
        """Load nodes into Neo4j"""
        print(f"📂 Loading nodes from {filepath}...")
        
        with open(filepath, 'r') as f:
            nodes = json.load(f)
        
        # Filter for clinically relevant nodes
        # 'kind' in nodes file matches what we saw
        relevant_kinds = {'Disease', 'Symptom', 'Compound', 'Side Effect', 'Pharmacologic Class'}
        filtered_nodes = [n for n in nodes if n['kind'] in relevant_kinds]
        
        print(f"Loading {len(filtered_nodes)} relevant nodes...")
        
        batch_size = 1000
        with self.driver.session() as session:
            for i in tqdm(range(0, len(filtered_nodes), batch_size), desc="Loading nodes"):
                batch = filtered_nodes[i:i+batch_size]
                
                # Dynamic label creation using apoc
                session.run("""
                    UNWIND $nodes AS node
                    CALL apoc.create.node([node.kind, 'Node'], {
                        id: node.id,
                        name: node.name
                    }) YIELD node AS n
                    RETURN count(n)
                """, nodes=batch)
                
    def load_edges(self, filepath="hetionet_edges_all.json"):
        """Load relationships into Neo4j"""
        print(f"📂 Loading edges from {filepath}...")
        
        with open(filepath, 'r') as f:
            edges = json.load(f)
            
        print(f"Found {len(edges)} total edges")
        
        # Filter relevant relationships
        # Keys to keep (Clinical focus)
        # CtD: Compound treats Disease
        # CpD: Compound palliates Disease
        # DpS: Disease presents Symptom
        # SeT: Side effect caused by Treatment (Compound)
        # DaG: Disease associates Gene
        
        relevant_types = ['CtD', 'CpD', 'DpS', 'SeT', 'DaG', 'DrD', 'DlA']
        
        # Check if key is 'kind' or 'metaedge' based on your check.py output
        key_name = 'metaedge' if 'metaedge' in edges[0] else 'kind'
        
        filtered_edges = [e for e in edges if e.get(key_name, '') in relevant_types]
        
        print(f"Loading {len(filtered_edges)} relevant edges (Disease-Symptom, Drug-Disease)...")
        
        batch_size = 1000
        with self.driver.session() as session:
            for i in tqdm(range(0, len(filtered_edges), batch_size), desc="Loading edges"):
                batch = filtered_edges[i:i+batch_size]
                
                # Using key_name dynamically
                query = f"""
                    UNWIND $edges AS edge
                    MATCH (source {{id: edge.source}})
                    MATCH (target {{id: edge.target}})
                    CALL apoc.create.relationship(source, edge.{key_name}, {{}}, target) YIELD rel
                    RETURN count(rel)
                """
                
                session.run(query, edges=batch)

def main():
    loader = HetionetLoader()
    try:
        loader.create_indexes()
        loader.load_nodes()
        loader.load_edges()
        print("\n✅ Knowledge Graph Built Successfully!")
    finally:
        loader.close()

if __name__ == "__main__":
    main()