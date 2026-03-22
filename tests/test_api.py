from fastapi.testclient import TestClient

from app.main import app
from app.tiny_text import TinyTextMode, transform_text
from app.transforms import CaseMode, ZalgoDirection, case_variants, slugify_text, text_stats, zalgo_text


client = TestClient(app)


def test_healthcheck_is_public() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_missing_api_key() -> None:
    response = client.post("/v1/tiny-text", json={"text": "Hello"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key."}


def test_transforms_text_with_default_mode() -> None:
    source_text = "Hello 123!"
    response = client.post(
        "/v1/tiny-text",
        headers={"X-API-Key": "test-key"},
        json={"text": source_text},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "superscript"
    assert body["tiny_text"] == transform_text(source_text, TinyTextMode.SUPERSCRIPT)
    assert body["variants"]["small_caps"] == transform_text(source_text, TinyTextMode.SMALL_CAPS)


def test_supports_bearer_auth_and_subscript_mode() -> None:
    source_text = "tag"
    response = client.post(
        "/v1/tiny-text",
        headers={"Authorization": "Bearer test-key"},
        json={"text": source_text, "mode": "subscript"},
    )

    assert response.status_code == 200
    assert response.json()["tiny_text"] == transform_text(source_text, TinyTextMode.SUBSCRIPT)


def test_zalgo_text_endpoint() -> None:
    response = client.post(
        "/v1/zalgo-text",
        headers={"X-API-Key": "test-key"},
        json={"text": "Hi", "intensity": 1, "direction": "up"},
    )

    assert response.status_code == 200
    assert response.json()["output_text"] == zalgo_text("Hi", 1, ZalgoDirection.UP)


def test_slugify_endpoint() -> None:
    response = client.post(
        "/v1/slugify",
        headers={"X-API-Key": "test-key"},
        json={"text": "Hello, API World!", "separator": "-", "lowercase": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["output_text"] == slugify_text("Hello, API World!", separator="-", lowercase=True)
    assert body["variants"]["snake"] == slugify_text("Hello, API World!", separator="_", lowercase=True)


def test_slugify_preserves_case_when_requested() -> None:
    response = client.post(
        "/v1/slugify",
        headers={"X-API-Key": "test-key"},
        json={"text": "Hello API", "separator": "-", "lowercase": False},
    )

    assert response.status_code == 200
    assert response.json()["output_text"] == "Hello-API"


def test_text_stats_endpoint() -> None:
    source_text = "Hello world.\nSecond line!"
    response = client.post(
        "/v1/text-stats",
        headers={"X-API-Key": "test-key"},
        json={"text": source_text},
    )

    assert response.status_code == 200
    assert response.json()["stats"] == text_stats(source_text)


def test_case_convert_endpoint() -> None:
    source_text = "hello api world"
    response = client.post(
        "/v1/case-convert",
        headers={"X-API-Key": "test-key"},
        json={"text": source_text, "mode": "camel"},
    )

    assert response.status_code == 200
    body = response.json()
    expected = case_variants(source_text)
    assert body["output_text"] == expected[CaseMode.CAMEL.value]
    assert body["variants"]["constant"] == expected[CaseMode.CONSTANT.value]
