import os
from google import genai
from dotenv import load_dotenv

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

class ContractAgent:
    def __init__(self):
        # 2. Configura a chave da API 
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Erro: GEMINI_API_KEY não encontrada no arquivo .env")
        
        # 3. Inicializa o NOVO cliente do Google (Padrão 2025/2026)
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-3.1-flash-lite'

    def generate_answer(self, question: str, retrieved_contexts: list) -> str:
        # Junta todos os textos que o Banco Vetorial encontrou
        context_text = "\n\n".join(retrieved_contexts)
        
        # O "System Prompt" (A regra de ouro exigida pela vaga)
        prompt = f"""
        Você é um assistente jurídico especialista em contratos imobiliários.
        Responda à pergunta do usuário baseando-se ÚNICA E EXCLUSIVAMENTE nos contextos fornecidos abaixo.
        Se a resposta não estiver nos contextos, diga: "Não encontrei essa informação nos contratos indexados."
        NÃO INVENTE INFORMAÇÕES.

        Contextos recuperados do banco:
        {context_text}

        Pergunta do Usuário: {question}
        
        Resposta:
        """
        
        # 4. Faz a chamada usando a nova estrutura da API
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        return response.text

if __name__ == "__main__":
    # Teste isolado do LLM
    agente = ContractAgent()
    
    contexto_mock = [
        "CLÁUSULA 5 - ENTREGA: Previsão Dezembro/2026. Tolerância 180 dias.",
        "CLÁUSULA 6 - DISTRATO: Multa de 20% sobre os valores pagos."
    ]
    pergunta = "Qual a multa se eu cancelar?"
    
    print("🤖 Processando com Gemini (Novo SDK Oficial)...")
    resposta = agente.generate_answer(pergunta, contexto_mock)
    print(f"\nResposta do Agente: {resposta}")