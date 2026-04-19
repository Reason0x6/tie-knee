from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.tiny_text import TinyTextMode, transform_text
from app.transforms import CaseMode, ZalgoDirection, case_variants, slugify_text, text_stats, zalgo_text


client = TestClient(app)


def test_root_returns_landing_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Text Utils API" in response.text
    assert "/docs" in response.text


def test_share_editor_page_is_available() -> None:
    response = client.get("/share")

    assert response.status_code == 200
    assert "Publish Share" in response.text
    assert "Overwrite Existing Share" in response.text
    assert "/v1/share" in response.text


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


def test_test_image_endpoint() -> None:
    response = client.get(
        "/v1/test-image",
        headers={"X-API-Key": "test-key"},
        params={"width": 320, "height": 180, "text": "Hello", "bg": "112233", "fg": "ffffff"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    image = Image.open(BytesIO(response.content))
    assert image.size == (320, 180)


def test_markdown_share_creation_and_render() -> None:
    slug = f"example-{uuid4().hex[:8]}"
    response = client.post(
        "/v1/share",
        headers={"X-API-Key": "test-key"},
        json={"slug": slug, "title": "Example Share", "markdown": "# Hello\n\nThis is **markdown**."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["share_url"] == f"https://tiny.vk2fgav.com/share/{slug}"
    assert body["overwritten"] is False

    api_response = client.get(f"/v1/share/{slug}")
    assert api_response.status_code == 200
    assert api_response.json()["markdown"] == "# Hello\n\nThis is **markdown**."

    page_response = client.get(f"/share/{slug}")
    assert page_response.status_code == 200
    assert "<h1>Hello</h1>" in page_response.text
    assert "Example Share" in page_response.text


def test_markdown_share_duplicate_slug_returns_conflict() -> None:
    slug = f"dupe-{uuid4().hex[:8]}"
    payload = {"slug": slug, "markdown": "first"}

    first_response = client.post("/v1/share", headers={"X-API-Key": "test-key"}, json=payload)
    second_response = client.post("/v1/share", headers={"X-API-Key": "test-key"}, json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert "overwrite=true" in second_response.json()["detail"]


def test_markdown_share_can_be_overwritten() -> None:
    slug = f"replace-{uuid4().hex[:8]}"
    first_payload = {"slug": slug, "title": "First", "markdown": "first"}
    second_payload = {"slug": slug, "title": "Second", "markdown": "second", "overwrite": True}

    first_response = client.post("/v1/share", headers={"X-API-Key": "test-key"}, json=first_payload)
    second_response = client.post("/v1/share", headers={"X-API-Key": "test-key"}, json=second_payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["overwritten"] is True

    fetch_response = client.get(f"/v1/share/{slug}")
    assert fetch_response.status_code == 200
    assert fetch_response.json()["title"] == "Second"
    assert fetch_response.json()["markdown"] == "second"
