"""LLM service tests: fallbacks must always protect the demo."""

from app.services import llm_service
from app.services.llm_service import ExtractedFields, build_fallback_explanation


def test_disabled_llm_falls_back(monkeypatch):
    monkeypatch.setattr(llm_service, "llm_available", lambda: False)
    explanation, used = llm_service.explain_recommendation({
        "recommended_mandi": "Baraut Mandi",
        "baseline_mandi": "Azadpur Mandi",
        "net_gain": 12050,
        "truck": "T104",
        "pool_farmer_count": 3,
        "is_return_trip": True,
        "spoilage_risk": "HIGH",
        "hours_remaining": 18,
    })
    assert used is False
    assert "Baraut Mandi" in explanation.headline
    assert "12050" in explanation.summary.replace(",", "").replace("₹", "")


def test_llm_failure_returns_fallback(monkeypatch):
    monkeypatch.setattr(llm_service, "llm_available", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_completion", lambda s, u: None)
    explanation, used = llm_service.explain_recommendation({"net_gain": 500})
    assert used is False
    assert explanation.headline


def test_invalid_json_returns_fallback(monkeypatch):
    monkeypatch.setattr(llm_service, "llm_available", lambda: True)
    monkeypatch.setattr(
        llm_service, "_chat_completion", lambda s, u: "not json at all {{{"
    )
    explanation, used = llm_service.explain_recommendation({"net_gain": 1})
    assert used is False


def test_schema_violation_returns_fallback(monkeypatch):
    monkeypatch.setattr(llm_service, "llm_available", lambda: True)

    def bad_payload(system, user):
        return '{"headline": 42, "summary": null}'

    monkeypatch.setattr(llm_service, "_chat_completion", bad_payload)
    explanation, used = llm_service.explain_recommendation({"net_gain": 5})
    assert used is False


def test_valid_structured_output_accepted(monkeypatch):
    monkeypatch.setattr(llm_service, "llm_available", lambda: True)
    payload = (
        '{"headline": "Pool and go.", "summary": "Gain ₹100.", '
        '"why_this_option": ["Higher net."], "action": "Join T104.", '
        '"urgency": "Move soon.", "warnings": []}'
    )
    monkeypatch.setattr(llm_service, "_chat_completion", lambda s, u: payload)
    explanation, used = llm_service.explain_recommendation({"net_gain": 100})
    assert used is True
    assert explanation.action == "Join T104."


def test_extraction_sanitises_numbers(monkeypatch):
    monkeypatch.setattr(llm_service, "llm_available", lambda: True)
    monkeypatch.setattr(
        llm_service,
        "_chat_completion",
        lambda s, u: '{"crop": "tomato", "quantity_kg": -50, "location_text": null}',
    )
    fields = llm_service.extract_fields("garbage")
    assert fields == ExtractedFields(crop="tomato")
