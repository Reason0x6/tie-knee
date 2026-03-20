from fastapi.testclient import TestClient

from app.main import app


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
    response = client.post(
        "/v1/tiny-text",
        headers={"X-API-Key": "test-key"},
        json={"text": "Hello 123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "superscript"
    assert body["tiny_text"] == "ᴴᵉˡˡᵒ ¹²³ᵎ"
    assert body["variants"]["small_caps"] == "Hᴇʟʟᴏ 123!"


def test_supports_bearer_auth_and_subscript_mode() -> None:
    response = client.post(
        "/v1/tiny-text",
        headers={"Authorization": "Bearer test-key"},
        json={"text": "tag", "mode": "subscript"},
    )

    assert response.status_code == 200
    assert response.json()["tiny_text"] == "ₜₐ𝓰"
