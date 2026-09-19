import os
import glob
import numpy as np
from google import genai
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.enabled = False
            return
            
        self.client = genai.Client(api_key=api_key)
        self.enabled = True
        self.embeddings = []
        self.chunks = []
        self.sources = []
        
        self._build_vector_store()
        
    def _build_vector_store(self):
        """Loads markdown clinical guidelines and embeds them into a Numpy Vector Store."""
        kb_path = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
        if not os.path.exists(kb_path):
            return
            
        print("Building RAG Vector Store from Clinical Guidelines...")
        md_files = glob.glob(os.path.join(kb_path, "*.md"))
        
        raw_texts = []
        for file_path in md_files:
            source_name = os.path.basename(file_path).replace(".md", "").replace("_", " ").title()
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Simple chunking by Markdown headers
                sections = content.split("\n## ")
                for i, section in enumerate(sections):
                    if not section.strip():
                        continue
                        
                    # Add back the header if it was split
                    text = section if i == 0 else f"## {section}"
                    raw_texts.append(text)
                    self.chunks.append(text)
                    self.sources.append(source_name)
                    
        if not raw_texts:
            return
            
        # Call Gemini Embedding API (Batch mode)
        # Using text-embedding-004 model
        try:
            response = self.client.models.embed_content(
                model='gemini-embedding-001',
                contents=raw_texts,
            )
            # Response returns a list of embeddings
            self.embeddings = np.array([e.values for e in response.embeddings])
            print(f"RAG Vector Store built successfully with {len(self.embeddings)} embedded guidelines.")
        except Exception as e:
            print(f"RAG Error during embedding generation: {e}")
            self.enabled = False

    def retrieve(self, query: str, top_k: int = 2):
        if not self.enabled or len(self.embeddings) == 0:
            return [], []
            
        # Embed the query
        try:
            response = self.client.models.embed_content(
                model='gemini-embedding-001',
                contents=query,
            )
            query_vector = np.array(response.embeddings[0].values)
            
            # Cosine Similarity: dot product of normalized vectors
            # Assuming vectors are already normalized by the API, but let's be safe
            q_norm = np.linalg.norm(query_vector)
            norms = np.linalg.norm(self.embeddings, axis=1)
            similarities = np.dot(self.embeddings, query_vector) / (norms * q_norm)
            
            # Get top K indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            retrieved_chunks = [self.chunks[i] for i in top_indices]
            retrieved_sources = [self.sources[i] for i in top_indices]
            
            return retrieved_chunks, retrieved_sources
            
        except Exception as e:
            print(f"RAG Retrieval Error: {e}")
            return [], []
