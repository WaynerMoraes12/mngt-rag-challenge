# MNGT RAG Engine

Sistema de consulta inteligente a contratos imobiliários em PDF, desenvolvido para o desafio técnico da Área Incrível · Grupo MNGT.

Permite fazer perguntas em linguagem natural sobre contratos indexados e receber respostas precisas com rastreabilidade direta ao trecho e ao documento de origem — sem inventar informações.

> **"Qual a multa por distrato do contrato de Maria Fernanda Santos?"**
> **"Quais contratos têm prazo de tolerância de 180 dias?"**

---

## Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose instalados
- Chave de API do Google Gemini — [obter gratuitamente aqui](https://aistudio.google.com/app/apikey)

---

## Execução

**1. Clone o repositório**
```bash
git clone https://github.com/WaynerMoraes12/mngt-rag-challenge.git
cd mngt-rag-challenge
```

**2. Configure as variáveis de ambiente**
```bash
cp .env.example .env
```
Edite o arquivo `.env` e adicione sua chave:
```
GEMINI_API_KEY=sua_chave_aqui
```

**3. Suba o sistema completo em segundo plano**
```bash
docker compose up --build -d
```

Na primeira execução o backend baixa o modelo de embeddings (~400MB). O frontend só inicializa após o backend estar saudável — isso é gerenciado automaticamente pelo healthcheck no compose.

Para acompanhar os logs enquanto os containers sobem:
```bash
docker compose logs -f
```

**4. Acesse**

| Serviço | URL |
|---|---|
| Interface web | http://localhost:5173 |
| Documentação da API | http://localhost:8000/docs |

---

## Como usar

1. Na barra lateral, faça upload de um contrato em PDF clicando em **Indexar Contrato**
2. O sistema extrai o texto, divide por cláusulas, indexa no banco vetorial e exibe um resumo automático com comprador, empreendimento, valor e prazo de entrega
3. No chat, faça perguntas em linguagem natural sobre qualquer contrato indexado
4. A resposta vem com as fontes rastreáveis — trecho exato e nome do contrato de origem
5. Para remover um contrato, clique no **X** ao lado do nome na lista da barra lateral

---

## Testes

Com o sistema rodando via Docker, execute os testes diretamente no container do backend:

```bash
docker compose exec backend pytest -v
```

Os testes cobrem: listagem de contratos, rejeição de arquivos não-PDF, fluxo completo de upload e exclusão com mocks, e validação de payload inválido.

---

## Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|---|---|---|
| `GEMINI_API_KEY` | Chave da API do Google Gemini | ✅ Sim |

Para trocar o provedor ou modelo de LLM, altere `self.model_id` e o cliente em `llm_agent.py`. A chave é sempre lida via variável de ambiente — nenhuma mudança de infraestrutura necessária.

---

## Arquitetura

```
┌──────────────────┐     HTTP      ┌─────────────────┐
│   React + Vite   │ ───────────► │    FastAPI      │
│   porta 5173     │              │    porta 8000   │
└──────────────────┘              └────────┬────────┘
                                           │
                       ┌───────────────────┼──────────────────┐
                       ▼                   ▼                  ▼
                pdf_processor        vector_store         llm_agent
                (chunking por        (embeddings          (Gemini +
                 cláusula)            ChromaDB)          prompt RAG)
```

**Fluxo de upload:**
PDF → `pdfplumber` extrai texto → divide por cláusulas via regex → gera embeddings locais → indexa no ChromaDB com metadados → Gemini sumariza comprador/valor/prazo → retorna resumo na interface

**Fluxo de pergunta:**
Pergunta → embedding da query → busca semântica no ChromaDB → injeta contexto + histórico no prompt → Gemini responde exclusivamente com base nos trechos recuperados → retorna resposta com fontes rastreáveis

---

## Estrutura do Repositório

```
.
├── main.py              # Rotas FastAPI: upload, ask, list, delete
├── pdf_processor.py     # Extração de texto e chunking por cláusula
├── vector_store.py      # Embeddings locais e interface com ChromaDB
├── llm_agent.py         # Prompt RAG, anti-alucinação e sumarização
├── test_main.py         # Testes de integração com mocks
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── frontend/
    ├── src/
    │   ├── App.tsx      # Interface de chat, upload e listagem
    │   ├── App.css
    │   └── main.tsx
    ├── Dockerfile
    └── package.json
```

---

## Decisões Técnicas

### Chunking por cláusula, não por tokens

Contratos imobiliários têm estrutura semântica previsível — `CLÁUSULA 4 – REAJUSTE`, `CLÁUSULA 6 – DISTRATO`. Dividir por contagem fixa de tokens quebraria cláusulas no meio, misturando contextos distintos no mesmo chunk e reduzindo a precisão da recuperação.

A estratégia em `pdf_processor.py` usa `re.split(r'(?i)(?=CLÁUSULA)')` para preservar cada cláusula como unidade semântica completa. Ao perguntar sobre distrato, o sistema recupera exatamente a cláusula de distrato — sem ruído de trechos adjacentes. Há fallback para parágrafos e linhas em documentos sem essa estrutura.

### ChromaDB como banco vetorial

Roda embutido no processo Python sem serviço adicional, persiste em disco via volume Docker nomeado e oferece API direta para `add`, `query` e `delete` por metadado. Para dezenas a centenas de contratos, não há ganho em soluções como Pinecone ou Qdrant — que adicionariam dependências de rede e configuração sem benefício mensurável nessa escala.

### `paraphrase-multilingual-MiniLM-L12-v2` para embeddings

Atende os três requisitos simultaneamente: suporte nativo a português, execução local sem chave de API e tamanho razoável (~120MB). Modelos maiores como `multilingual-e5-large` produziriam embeddings de melhor qualidade, mas aumentariam o tempo de inicialização do container — tradeoff desfavorável para este contexto.

### Google Gemini como LLM

Custo zero no tier gratuito e qualidade suficiente para extração de informação estruturada de contratos jurídicos. Modelo e chave são configuráveis via variável de ambiente — trocar por OpenAI ou Anthropic exige apenas mudar `GEMINI_API_KEY` e duas linhas em `llm_agent.py`.

### Anti-alucinação por prompt restritivo

O modelo é instruído a responder baseando-se **exclusivamente** no contexto recuperado e a retornar uma mensagem padrão quando a informação não existe nos contratos. `temperature=0.1` reduz variabilidade. O contexto é injetado com o nome do documento de origem (`[Documento: CVV-2024-0312.pdf]`) para rastreabilidade completa na resposta.

### Histórico multiturno no prompt, não em banco

O histórico da conversa é enviado pelo frontend a cada requisição e injetado diretamente no prompt. Isso mantém a API stateless — sem complexidade de gerenciamento de sessão no backend — e garante que qualquer instância possa atender qualquer requisição sem estado compartilhado.

### Volume persistente para uploads e banco vetorial

Tanto o ChromaDB (`chroma_data/`) quanto os PDFs indexados (`uploads/`) são persistidos via volumes Docker nomeados. Isso garante que reinicializações do container não causem inconsistência entre os vetores indexados e os arquivos de origem.

---

## Diferenciais Implementados

- ✅ **Sumarização automática ao indexar** — extrai comprador, empreendimento, valor e prazo de entrega via LLM no momento do upload
- ✅ **Histórico multiturno** — contexto da conversa é mantido e enviado a cada pergunta
- ✅ **Testes automatizados** — `pytest` com mocks para isolar dependências externas (LLM e processamento de PDF)
