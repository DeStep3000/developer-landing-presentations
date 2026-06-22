import json

import pytest


@pytest.mark.django_db
def test_swagger_docs_are_available(client):
    response = client.get("/api/docs")

    assert response.status_code == 200
    assert b"swagger" in response.content.lower()


@pytest.mark.django_db
def test_openapi_schema_is_available(client):
    response = client.get("/api/schema")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/vnd.oai.openapi")


@pytest.mark.django_db
def test_contact_endpoints_have_swagger_descriptions(client):
    response = client.get("/api/schema?format=json")

    assert response.status_code == 200

    schema = json.loads(response.content)
    contact = schema["paths"]["/api/contact"]
    health = schema["paths"]["/api/health"]
    metrics = schema["paths"]["/api/metrics"]

    assert contact["post"]["summary"] == "Отправить заявку с лендинга"
    assert "AI-анализ" in contact["post"]["description"]
    assert health["get"]["summary"] == "Проверить состояние API"
    assert metrics["get"]["summary"] == "Получить статистику обращений"
