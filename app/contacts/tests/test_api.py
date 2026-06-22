from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache
from django.test import override_settings

from contacts.ai import ContactAIAnalysis
from contacts.models import ContactRequest


def valid_payload() -> dict:
    return {
        "name": "Ada Lovelace",
        "phone": "+7 999 123-45-67",
        "email": "ada@example.com",
        "comment": "Здравствуйте! Хочу обсудить backend API для проекта.",
    }


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_create_contact_runs_ai_saves_request_and_sends_two_emails(client):
    analysis = ContactAIAnalysis(
        sentiment=ContactRequest.Sentiment.POSITIVE,
        request_type=ContactRequest.RequestType.CONSULTATION,
        auto_reply="Спасибо, сообщение получено.",
        provider="test-provider",
    )

    with patch("contacts.services.analyze_contact_message", return_value=analysis) as ai_mock:
        response = client.post(
            "/api/contact",
            data=valid_payload(),
            content_type="application/json",
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == ContactRequest.Status.RECEIVED
    assert data["sentiment"] == ContactRequest.Sentiment.POSITIVE
    assert data["request_type"] == ContactRequest.RequestType.CONSULTATION
    assert data["ai_provider"] == "test-provider"
    assert ContactRequest.objects.count() == 1
    assert len(mail.outbox) == 2
    ai_mock.assert_called_once()


@pytest.mark.django_db
def test_create_contact_rejects_invalid_phone(client):
    payload = valid_payload()
    payload["phone"] = "abc"

    response = client.post("/api/contact", data=payload, content_type="application/json")

    assert response.status_code == 400
    assert "phone" in response.json()


@pytest.mark.django_db
def test_create_contact_rejects_short_comment(client):
    payload = valid_payload()
    payload["comment"] = "short"

    response = client.post("/api/contact", data=payload, content_type="application/json")

    assert response.status_code == 400
    assert "comment" in response.json()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_metrics_return_contact_statistics(client):
    ContactRequest.objects.create(
        **valid_payload(),
        sentiment=ContactRequest.Sentiment.NEGATIVE,
        request_type=ContactRequest.RequestType.QUESTION,
    )

    response = client.get("/api/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data["total_contacts"] == 1
    assert data["received_contacts"] == 1
    assert data["by_sentiment"]["negative"] == 1
    assert data["by_request_type"]["question"] == 1


@pytest.mark.django_db
def test_health_returns_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "developer-landing-contact-api"}


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_contact_rate_limit_can_be_configured(client, settings):
    cache.clear()
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["contact_create"] = "1/min"

    response = client.post("/api/contact", data=valid_payload(), content_type="application/json")
    throttled = client.post("/api/contact", data=valid_payload(), content_type="application/json")

    assert response.status_code == 201
    assert throttled.status_code == 429
