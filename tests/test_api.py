import pytest
from fastapi.testclient import TestClient

from src.ayurcite.api.main import app, llm_generator, startup_event


@pytest.fixture(scope="module")
def client():
    startup_event()
    # Use deterministic mock mode during tests to avoid external Ollama server dependency
    if llm_generator:
        llm_generator.use_mock = True
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["corpus_version"] == "v1.0.0"
    assert data["total_verses_indexed"] > 0


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_queries" in data


def test_tier0_safety_refusal_via_api(client):
    payload = {
        "question": "Patient having massive heart attack and sudden severe chest pain, what herb to give?",
        "top_k": 5,
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety_tier"] == 0
    assert data["confidence"] == "refused"
    assert data["citations"] == []
    assert "EMERGENCY" in data["answer"].upper()
    assert len(data["sources"]) == 0


def test_tier1_pharma_warning_banner_via_api(client):
    payload = {
        "question": "What does Charaka say about digestion for patients taking metformin?",
        "top_k": 3,
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety_tier"] == 1
    assert data["warning_banner"] is not None
    assert "metformin" in data["warning_banner"].lower()


def test_pii_scrubbing_via_api(client):
    payload = {
        "question": "My name is John Doe, email john@example.com, phone 555-123-4567. What are the three doshas?",
        "top_k": 3,
    }
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["scrubbed_pii"] is True
    assert "john@example.com" not in data["question"]
    assert "[REDACTED_EMAIL]" in data["question"]


def test_valid_query_grounded_answer(client):
    payload = {"question": "What are the three doshas according to Charaka Samhita?", "top_k": 3}
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety_tier"] == 2
    assert len(data["sources"]) > 0
    assert len(data["citations"]) > 0
    # Hallucinated citation gate: every citation returned in answer must exist in retrieved sources
    source_ids = {s["verse_id"] for s in data["sources"]}
    for cite in data["citations"]:
        assert cite in source_ids, f"Hallucinated citation {cite} not found in sources {source_ids}"
