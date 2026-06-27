import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_listar_contratos_retorna_sucesso():
    response = client.get("/api/contracts")
    assert response.status_code == 200
    assert "contracts" in response.json()
    assert isinstance(response.json()["contracts"], list)

def test_upload_rejeita_arquivo_falso():
    response = client.post(
        "/api/upload",
        files={"file": ("hack.txt", b"Codigo malicioso", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Apenas PDF"

@patch("main.process_contract")
@patch("main.agent.summarize_contract")
def test_upload_e_delete_fluxo_completo(mock_summarize, mock_process):
    mock_process.return_value = ["CLÁUSULA 1 - TESTE: Conteúdo fake."]
    mock_summarize.return_value = "Resumo fake gerado pelo teste."
    
    pdf_falso = io.BytesIO(b"%PDF-1.4 mock pdf content")
    
    upload_resp = client.post(
        "/api/upload",
        files={"file": ("contrato_teste.pdf", pdf_falso, "application/pdf")}
    )
    
    assert upload_resp.status_code == 200
    
    delete_resp = client.delete("/api/contracts/contrato_teste.pdf")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "removido"

def test_pergunta_sem_payload_gera_erro():
    response = client.post("/api/ask", json={"duvida": "Qual a multa?"})
    assert response.status_code == 422