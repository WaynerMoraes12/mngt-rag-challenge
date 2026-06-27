import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class ContractAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY ausente no arquivo .env")

        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-3.1-flash-lite'

    def summarize_contract(self, chunks: list[str]) -> str:
        
        full_text = "\n".join(chunks[:5]) 
        prompt = f"""
        Analise o início deste contrato e extraia de forma direta e curta:
        - Comprador
        - Empreendimento
        - Valor (se houver)
        - Prazo de entrega (se houver)
        
        Texto do Contrato: {full_text}
        """
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        return response.text

    def generate_answer(self, question: str, context: list[str], history: list[dict] = None) -> str:
        context_str = "\n\n".join(context)
        
        system_prompt = f"""
        Você é um assistente jurídico especializado em contratos imobiliários.
        Responda à pergunta do usuário baseando-se EXCLUSIVAMENTE no contexto da busca atual.
        Se a resposta não estiver no contexto, responda: 'Não encontrei essa informação nos contratos indexados.'
        
        Contexto da busca atual:
        {context_str}
        """
        
        history_text = ""
        if history:
            history_text = "Histórico da Conversa:\n"
            for msg in history:
                role = "Usuário" if msg['sender'] == 'user' else "Assistente"
                history_text += f"{role}: {msg['text']}\n"
        
        final_prompt = f"{system_prompt}\n\n{history_text}\nUsuário: {question}\nAssistente:"
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=final_prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        
        return response.text