import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from pdf_processor import process_contract
from vector_store import VectorStore
from llm_agent import ContractAgent

app = FastAPI(title="MNGT Contract API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = VectorStore()
agent = ContractAgent()

os.makedirs("uploads", exist_ok=True)

class MessageHistory(BaseModel):
    sender: str
    text: str

class AskRequest(BaseModel):
    question: str
    history: List[MessageHistory] = []

class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@app.get("/api/contracts")
async def list_contracts():
    files = [f for f in os.listdir("uploads") if f.endswith(".pdf")]
    return {"contracts": files}

@app.delete("/api/contracts/{filename}")
async def delete_contract(filename: str):
    file_path = f"uploads/{filename}"
    if os.path.exists(file_path):
        os.remove(file_path)
        db.delete_source(filename)
        return {"status": "removido"}
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@app.post("/api/upload")
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas PDF")

    safe_name = Path(file.filename).name
    file_path = f"uploads/{safe_name}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        clausulas = process_contract(file_path)
        if not clausulas:
            raise HTTPException(status_code=400, detail="PDF vazio ou ilegível")
            
        db.index_chunks(clausulas, source_file=safe_name)
        resumo = agent.summarize_contract(clausulas)
        
        return {
            "status": "sucesso", 
            "mensagem": f"Indexado: {safe_name}",
            "resumo": resumo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    try:
        resultados = db.search(request.question, n_results=10)
        contextos = resultados['documents'][0]
        metadados = resultados['metadatas'][0]
        
        if not contextos:
            return AskResponse(answer="Banco de dados vazio.", sources=[])
        
        contextos_enriquecidos = [
            f"[Documento: {meta['source']}] {ctx}"
            for ctx, meta in zip(contextos, metadados)
        ]
        
        hist_dicts = [{"sender": m.sender, "text": m.text} for m in request.history]
        resposta = agent.generate_answer(request.question, contextos_enriquecidos, hist_dicts)
        
        fontes = [
            {
                "contrato": meta['source'],
                "trecho": meta['chunk_index'],
                "texto_original": ctx
            }
            for ctx, meta in zip(contextos, metadados)
        ]
            
        return AskResponse(answer=resposta, sources=fontes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))