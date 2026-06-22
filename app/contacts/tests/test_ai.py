from contacts.ai import fallback_analysis, parse_ai_json
from contacts.models import ContactRequest


def test_fallback_analysis_classifies_consultation_and_positive_sentiment():
    result = fallback_analysis(
        "Спасибо, отличный сайт. Хочу обсудить проект и консультацию.",
        "test fallback",
    )

    assert result.sentiment == ContactRequest.Sentiment.POSITIVE
    assert result.request_type == ContactRequest.RequestType.CONSULTATION
    assert result.provider == "fallback:rules"
    assert result.fallback_reason == "test fallback"


def test_parse_ai_json_accepts_markdown_json_block():
    payload = parse_ai_json('```json\n{"sentiment":"neutral","request_type":"question"}\n```')

    assert payload["sentiment"] == "neutral"
    assert payload["request_type"] == "question"
