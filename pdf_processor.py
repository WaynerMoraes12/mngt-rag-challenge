import re
import pdfplumber
from typing import List, Dict, Any

def extract_text_from_pdf(file_path: str) -> str:
    full_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                full_text += extracted + "\n"
    return full_text

def chunk_text_by_clause(text: str) -> List[Dict[str, Any]]:
    pattern = re.compile(r'(?i)(CL[ÁA]USULA\s+.*?)(?=CL[ÁA]USULA\s+|$)', re.DOTALL)
    matches = pattern.findall(text)
    
    chunks = []
    for index, match in enumerate(matches):
        clean_text = match.strip()
        if clean_text:
            chunks.append({
                "chunk_index": index + 1,
                "text": clean_text,
                "word_count": len(clean_text.split())
            })
    return chunks

def process_contract(file_path: str) -> List[Dict[str, Any]]:
    raw_text = extract_text_from_pdf(file_path)
    clauses = chunk_text_by_clause(raw_text)
    return clauses

if __name__ == "__main__":
    arquivo_teste = "contrato.pdf"
    
    try:
        resultado = process_contract(arquivo_teste)
        for chunk in resultado:
            print(f"--- Cláusula {chunk['chunk_index']} ({chunk['word_count']} palavras) ---")
            print(chunk['text'][:150] + "...\n")
    except FileNotFoundError:
        pass