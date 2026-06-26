import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_data"):
        self.embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="contratos_mngt")

    def index_chunks(self, chunks: List[Dict[str, Any]], source_file: str) -> None:
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{source_file}_clause_{chunk['chunk_index']}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            metadatas.append({
                "source": source_file,
                "chunk_index": chunk['chunk_index'],
                "word_count": chunk['word_count']
            })

        embeddings = self.embedding_model.encode(documents).tolist()

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search(self, query: str, n_results: int = 1) -> Dict[str, Any]:
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return results

if __name__ == "__main__":
    from pdf_processor import process_contract

    arquivo_alvo = "contrato.pdf"
    clausulas = process_contract(arquivo_alvo)

    print("Carregando o Motor de IA Multilingue e Banco Vetorial...")
    db = VectorStore()

    print("Indexando as clausulas no ChromaDB...")
    db.index_chunks(clausulas, arquivo_alvo)

    pergunta_usuario = "O que acontece se eu quiser cancelar e fizer o distrato?"
    print(f"\nUsuario: '{pergunta_usuario}'")
    
    resposta_banco = db.search(pergunta_usuario)
    
    print("\nBanco Vetorial encontrou o trecho mais relevante:")
    print(f"Fonte: {resposta_banco['metadatas'][0][0]['source']} | Clausula {resposta_banco['metadatas'][0][0]['chunk_index']}")
    print(f"Texto: {resposta_banco['documents'][0][0]}")