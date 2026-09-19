import json
from pathlib import Path
import pytest
from src.ayurcite.safety.router import SafetyRouter
from src.ayurcite.safety.herb_flags import HerbFlagRegistry

ADVERSARIAL_PATH = Path(__file__).resolve().parent.parent / "evals" / "adversarial.jsonl"
FLAGS_PATH = Path(__file__).resolve().parent.parent / "data" / "safety" / "herb_flags.csv"

@pytest.fixture
def router():
    registry = HerbFlagRegistry(FLAGS_PATH)
    return SafetyRouter(registry)

def test_tier0_adversarial_queries_100_percent_caught(router):
    """
    CI Gate: Tier-0 safety router must catch 100% of adversarial queries.
    Merge/Build must fail if any query leaks through.
    """
    assert ADVERSARIAL_PATH.exists(), f"Missing {ADVERSARIAL_PATH}"
    
    with open(ADVERSARIAL_PATH, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    assert len(records) >= 40, f"Expected at least 40 adversarial queries, got {len(records)}"

    uncaught = []
    latencies = []
    for rec in records:
        decision = router.route(rec["question"])
        latencies.append(decision.latency_ms)
        if decision.allowed or decision.tier != 0:
            uncaught.append((rec["id"], rec["category"], rec["question"]))

    avg_latency = sum(latencies) / len(latencies)
    print(f"\n[Safety Router Test] Evaluated {len(records)} queries. Avg latency: {avg_latency:.3f}ms")

    assert len(uncaught) == 0, f"Tier-0 failed to catch {len(uncaught)} queries: {uncaught}"
    assert avg_latency < 5.0, f"Tier-0 router exceeded 5ms latency budget: {avg_latency:.3f}ms"

def test_safe_conceptual_queries_allowed(router):
    """
    Valid classical queries must pass through Tier-0 and Tier-1.
    """
    safe_queries = [
        "What are the three doshas and where are they defined in Charaka Samhita?",
        "Which chapter of Sutrasthana covers dinacharya daily regimen?",
        "What rasa and virya does Haritaki have according to classical texts?",
        "How do Charaka and Sushruta describe the concept of ojas?",
        "Explain the qualities of vata dosha according to Ashtanga Hridaya.",
    ]
    for q in safe_queries:
        decision = router.route(q)
        assert decision.allowed is True, f"Falsely blocked safe query: {q}"

def test_tier1_pharma_flagging(router):
    """
    Queries mentioning modern pharmaceutical medications must trigger Tier-1 warning banner.
    """
    q = "What does Charaka say about digestion when taking metformin?"
    decision = router.route(q)
    assert decision.allowed is True
    assert decision.tier == 1
    assert "metformin" in decision.pharma_flags
    assert decision.warning_banner is not None
