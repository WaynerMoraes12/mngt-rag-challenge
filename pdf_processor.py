import pdfplumber
import re

def process_contract(file_path: str) -> list[str]:
    full_text = ""
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    full_text = full_text.strip()
    
    if not full_text:
        return []

    if "CLÁUSULA" in full_text.upper():
        raw_chunks = re.split(r'(?i)(?=CLÁUSULA)', full_text)
        return [c.strip() for c in raw_chunks if c.strip()]
    
    paragraphs = re.split(r'\n\s*\n', full_text)
    if len(paragraphs) > 1:
        return [p.strip() for p in paragraphs if p.strip()]
    
    lines = full_text.split('\n')
    return [line.strip() for line in lines if line.strip()]