import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

def extract_clause_name(chunk: str) -> str:
    match = re.match(r'(?i)(CLÁUSULA\s+[\dIVXLC]+[^\n]*)', chunk)
    return match.group(1).strip() if match else "Trecho sem título explícito"

class VectorStore:
    def __init__(self):
        os.makedirs("chroma_data", exist_ok=True)
        self.client = chromadb.PersistentClient(path="./chroma_data")
        self.collection = self.client.get_or_create_collection(name="mngt_contracts")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    def index_chunks(self, chunks: list[str], source_file: str):
        if not chunks:
            return
            
        self.collection.delete(where={"source": source_file})
        
        embeddings = self.model.encode(chunks).tolist()
        metadatas = [{"source": source_file, "chunk_index": extract_clause_name(c)} for c in chunks]
        ids = [f"{source_file}_chunk_{i+1}" for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, n_results: int = 10):
        count = self.collection.count()
        if count == 0:
            return {'documents': [[]], 'metadatas': [[]]}
            
        limit = min(n_results, count)
        query_embedding = self.model.encode([query]).tolist()
        
        return self.collection.query(
            query_embeddings=query_embedding,
            n_results=limit
        )
        
    def delete_source(self, source_file: str):
        self.collection.delete(where={"source": source_file})