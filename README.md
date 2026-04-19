# Text Utils API

Small FastAPI service for text transformations, markdown sharing, and analysis. It includes unicode styling, zalgo text generation, slug creation, text statistics, case conversion, placeholder image generation, and persistent pastebin-style markdown shares behind API key authentication where appropriate.

## Features

- `POST /v1/tiny-text`
- `POST /v1/zalgo-text`
- `POST /v1/slugify`
- `POST /v1/text-stats`
- `POST /v1/case-convert`
- `GET /v1/test-image`
- `POST /v1/share`
- `GET /v1/share/{slug}`
- `GET /share`
- `GET /share/{slug}`
- `X-API-Key` and `Authorization: Bearer ...` auth support
- Dockerized for local runs and GHCR publishing
- GitHub Actions workflow for image builds on `main`

## Endpoints

- `POST /v1/tiny-text`: tiny unicode variants with `superscript`, `small_caps`, and `subscript`
- `POST /v1/zalgo-text`: adds combining marks for glitch-style text
- `POST /v1/slugify`: generates URL-safe slugs
- `POST /v1/text-stats`: returns word, sentence, line, and character counts
- `POST /v1/case-convert`: converts text into common naming and display cases
- `GET /v1/test-image`: generates configurable placeholder PNGs similar to `placehold.co`
- `POST /v1/share`: creates a persistent markdown share for a chosen slug and can explicitly overwrite an existing slug
- `GET /v1/share/{slug}`: returns stored markdown share metadata and content as JSON
- `GET /share`: pastebin-style frontend for creating shares
- `GET /share/{slug}`: public rendered markdown page for a stored share

## Request examples

Tiny text:

```bash
curl -X POST http://localhost:8000/v1/tiny-text \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d "{\"text\":\"Hello world!\",\"mode\":\"superscript\"}"
```

Example response:

```json
{
  "input_text": "Hello world!",
  "mode": "superscript",
  "tiny_text": "ᴴᵉˡˡᵒ ʷᵒʳˡᵈᵎ",
  "variants": {
    "small_caps": "Hᴇʟʟᴏ ᴡᴏʀʟᴅ!",
    "superscript": "ᴴᵉˡˡᵒ ʷᵒʳˡᵈᵎ",
    "subscript": "ₕₑₗₗₒ 𝓌ₒᵣₗ𝒹!"
  }
}
```

Slugify:

```bash
curl -X POST http://localhost:8000/v1/slugify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d "{\"text\":\"Hello, API World!\",\"separator\":\"-\",\"lowercase\":true}"
```

Text stats:

```bash
curl -X POST http://localhost:8000/v1/text-stats \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d "{\"text\":\"Hello world. Second line!\"}"
```

Test image:

```bash
curl "http://localhost:8000/v1/test-image?width=600&height=300&text=Hello&bg=f4efe7&fg=1f1d1a" \
  -H "X-API-Key: dev-key-change-me" \
  --output placeholder.png
```

Markdown share:

```bash
curl -X POST http://localhost:8000/v1/share \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d "{\"slug\":\"example\",\"title\":\"Example Share\",\"markdown\":\"# Hello\\n\\nThis is **markdown**.\"}"
```

Overwrite an existing slug:

```bash
curl -X POST http://localhost:8000/v1/share \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d "{\"slug\":\"example\",\"title\":\"Updated Share\",\"markdown\":\"Updated body\",\"overwrite\":true}"
```

Example share URL:

```text
https://tiny.vk2fgav.com/share/example
```

## Local run

1. Copy the example env and set an API key:

```powershell
Copy-Item .env.example .env
$env:API_KEYS="dev-key-change-me"
$env:SHARE_BASE_URL="https://tiny.vk2fgav.com"
```

2. Install dependencies and start the server:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with Swagger docs at `http://localhost:8000/docs`.
The share editor will be available at `http://localhost:8000/share`.

## Docker

```bash
docker compose up --build
```

The compose service name is `text-utils-api`.
The default compose setup mounts `./data` into the container so markdown shares persist across restarts.

## GHCR publishing

The workflow at `.github/workflows/ghcr.yml` builds and pushes the image to:

```text
ghcr.io/<your-github-owner>/text-utils-api
```

To make that work:

1. Push this project to a GitHub repository.
2. Ensure GitHub Actions is enabled.
3. Keep the workflow permission to write packages enabled for the repository.

The workflow uses the built-in `GITHUB_TOKEN`, so no separate registry password is required for the push.
