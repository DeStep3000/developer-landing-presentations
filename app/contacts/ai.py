import json
import logging
from dataclasses import dataclass

from django.conf import settings

from contacts.models import ContactRequest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContactAIAnalysis:
    sentiment: str
    request_type: str
    auto_reply: str
    provider: str
    fallback_reason: str = ""


SYSTEM_PROMPT = (
    "You are an assistant for a developer portfolio landing page backend. "
    "Analyze a contact form message. Return only JSON with keys: "
    "sentiment, request_type, auto_reply. sentiment must be one of "
    "positive, neutral, negative. request_type must be one of job_offer, "
    "consultation, feedback, question, other. auto_reply must be a concise "
    "polite Russian response confirming that the message was received."
)


def analyze_contact_message(name: str, email: str, comment: str) -> ContactAIAnalysis:
    if not settings.OPENAI_API_KEY:
        return fallback_analysis(comment, "OPENAI_API_KEY is not configured")

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Name: {name}\nEmail: {email}\nComment:\n{comment}\n\nReturn JSON only."
                    ),
                },
            ],
        )
        payload = parse_ai_json(response.output_text)
        return ContactAIAnalysis(
            sentiment=normalize_choice(
                payload.get("sentiment"),
                ContactRequest.Sentiment.values,
                ContactRequest.Sentiment.NEUTRAL,
            ),
            request_type=normalize_choice(
                payload.get("request_type"),
                ContactRequest.RequestType.values,
                ContactRequest.RequestType.OTHER,
            ),
            auto_reply=str(payload.get("auto_reply") or default_reply()),
            provider=f"openai:{settings.OPENAI_MODEL}",
        )
    except Exception as exc:  # noqa: BLE001 - fallback must keep the API available.
        logger.warning("ai analysis failed, fallback is used", exc_info=exc)
        return fallback_analysis(comment, f"{type(exc).__name__}: {exc}")


def parse_ai_json(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def normalize_choice(value: str | None, allowed: list[str], default: str) -> str:
    if value in allowed:
        return value
    return default


def fallback_analysis(comment: str, reason: str) -> ContactAIAnalysis:
    lowered = comment.lower()
    negative_markers = ("плохо", "ошибка", "не работает", "проблем", "bad", "bug", "fail")
    positive_markers = ("спасибо", "отлично", "класс", "нравится", "great", "thanks")

    if any(marker in lowered for marker in negative_markers):
        sentiment = ContactRequest.Sentiment.NEGATIVE
    elif any(marker in lowered for marker in positive_markers):
        sentiment = ContactRequest.Sentiment.POSITIVE
    else:
        sentiment = ContactRequest.Sentiment.NEUTRAL

    if any(marker in lowered for marker in ("работ", "вакан", "job", "hire", "offer")):
        request_type = ContactRequest.RequestType.JOB_OFFER
    elif any(marker in lowered for marker in ("консультац", "проект", "заказ", "consult")):
        request_type = ContactRequest.RequestType.CONSULTATION
    elif any(marker in lowered for marker in ("отзыв", "feedback")):
        request_type = ContactRequest.RequestType.FEEDBACK
    elif "?" in lowered or any(marker in lowered for marker in ("вопрос", "question")):
        request_type = ContactRequest.RequestType.QUESTION
    else:
        request_type = ContactRequest.RequestType.OTHER

    return ContactAIAnalysis(
        sentiment=sentiment,
        request_type=request_type,
        auto_reply=default_reply(),
        provider="fallback:rules",
        fallback_reason=reason[:255],
    )


def default_reply() -> str:
    return (
        "Спасибо за обращение. Я получил сообщение, изучу детали и отвечу "
        "на указанный email в ближайшее время."
    )
