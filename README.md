# Text Utils API

Small FastAPI service for text transformations and analysis. It includes unicode styling, zalgo text generation, slug creation, text statistics, and case conversion behind API key authentication.

## Features

- `POST /v1/tiny-text`
- `POST /v1/zalgo-text`
- `POST /v1/slugify`
- `POST /v1/text-stats`
- `POST /v1/case-convert`
- `X-API-Key` and `Authorization: Bearer ...` auth support
- Dockerized for local runs and GHCR publishing
- GitHub Actions workflow for image builds on `main`

## Endpoints

- `POST /v1/tiny-text`: tiny unicode variants with `superscript`, `small_caps`, and `subscript`
- `POST /v1/zalgo-text`: adds combining marks for glitch-style text
- `POST /v1/slugify`: generates URL-safe slugs
- `POST /v1/text-stats`: returns word, sentence, line, and character counts
- `POST /v1/case-convert`: converts text into common naming and display cases

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

## Local run

1. Copy the example env and set an API key:

```powershell
Copy-Item .env.example .env
$env:API_KEYS="dev-key-change-me"
```

2. Install dependencies and start the server:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with Swagger docs at `http://localhost:8000/docs`.

## Docker

```bash
docker compose up --build
```

The compose service name is `text-utils-api`.

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
