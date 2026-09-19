from src.ayurcite.generate.validator import validate_response

def test_validator_valid_answer():
    retrieved = {"cs_su_01_015", "cs_su_01_016"}
    answer = (
        "According to Charaka Samhita, the doshas are three: vata, pitta, and kapha [cs_su_01_015]. "
        "When in balance, they sustain normal physiological function [cs_su_01_016]."
    )
    result = validate_response(answer, retrieved)
    assert result.is_valid is True
    assert result.hallucinated_citations == []
    assert set(result.extracted_citations) == retrieved

def test_validator_hallucinated_citation_rejected():
    retrieved = {"cs_su_01_015"}
    answer = (
        "Vata is described here [cs_su_01_015], but another text mentions it elsewhere [cs_su_02_099]."
    )
    result = validate_response(answer, retrieved)
    assert result.is_valid is False
    assert "cs_su_02_099" in result.hallucinated_citations

def test_validator_second_person_instruction_rejected():
    retrieved = {"cs_su_01_015"}
    # Contains forbidden prescriptive "you should take"
    answer = (
        "For sluggish digestion, you should take 5 grams of Haritaki powder daily [cs_su_01_015]."
    )
    result = validate_response(answer, retrieved)
    assert result.is_valid is False
    assert "second-person" in result.reason.lower() or "prescriptive" in result.reason.lower()

def test_validator_classical_factual_dosage_allowed():
    retrieved = {"cs_su_01_015"}
    # Classical factual report of text contents without second-person advice
    answer = (
        "The classical text records that the formulation was prepared with four palas of ghee [cs_su_01_015]."
    )
    result = validate_response(answer, retrieved)
    assert result.is_valid is True
