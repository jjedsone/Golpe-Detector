"""
Testes automatizados para a API
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Testa health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data

def test_submit_invalid_url():
    """Testa envio de URL inválida"""
    response = client.post("/submit", json={"url": "http://localhost"})
    assert response.status_code == 400

def test_submit_valid_url():
    """Testa envio de URL válida"""
    response = client.post("/submit", json={
        "url": "https://google.com",
        "user_id": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    assert data["status"] == "enfileirado"

def test_get_submission_not_found():
    """Testa busca de submissão inexistente"""
    response = client.get("/submission/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_get_submissions():
    """Testa listagem de submissões"""
    response = client.get("/submissions")
    assert response.status_code == 200
    data = response.json()
    assert "submissions" in data
    assert "total" in data

def test_get_stats():
    """Testa estatísticas"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "done" in data

def test_metrics():
    """Testa endpoint de métricas"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "requests_total" in data

