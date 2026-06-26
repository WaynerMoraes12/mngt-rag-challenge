import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

# Importando os nossos módulos
from pdf_processor import process_contract
from vector_store import VectorStore
from llm_agent import ContractAgent

app = FastAPI(title="MNGT Contract RAG API")

# Inicializando os nossos motores
db = VectorStore()
agent = ContractAgent()

# Garantir que a pasta de uploads temporários exista
os.makedirs("uploads", exist_ok=True)

# Tipagem estrita com Pydantic (Exigência da Vaga)
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@app.post("/api/upload")
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")

    file_path = f"uploads/{file.filename}"
    
    # 1. Salvar o arquivo localmente
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Processar (Fatiamento Inteligente)
        clausulas = process_contract(file_path)
        
        # 3. Indexar no Banco Vetorial
        db.index_chunks(clausulas, source_file=file.filename)
        
        return {"status": "sucesso", "mensagem": f"{file.filename} indexado com {len(clausulas)} cláusulas."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    try:
        # 1. Buscar as 3 cláusulas mais relevantes no Banco Vetorial (Busca Semântica)
        resultados_banco = db.search(request.question, n_results=3)
        
        # 2. Formatar os contextos recuperados para o LLM
        contextos_recuperados = resultados_banco['documents'][0]
        metadados = resultados_banco['metadatas'][0]
        
        # 3. Gerar a resposta com o Gemini
        resposta_llm = agent.generate_answer(request.question, contextos_recuperados)
        
        # 4. Estruturar as fontes para o Front-end mostrar na tela (Exigência do Desafio)
        fontes = []
        for i in range(len(contextos_recuperados)):
            fontes.append({
                "contrato": metadados[i]['source'],
                "clausula": metadados[i]['chunk_index'],
                "texto_original": contextos_recuperados[i]
            })
            
        return AskResponse(answer=resposta_llm, sources=fontes)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))