from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.auth import require_api_key
from app.config import get_settings
from app.tiny_text import TinyTextMode, all_variants
from app.transforms import (
    CaseMode,
    ZalgoDirection,
    case_variants,
    slugify_text,
    text_stats,
    zalgo_text,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if not settings.api_keys:
        raise RuntimeError("API_KEYS must be configured before the service can start.")
    yield


app = FastAPI(
    title="Text Utils API",
    version="1.0.0",
    description=(
        "General-purpose text utility API for unicode transforms, slug generation, "
        "text analysis, and case conversion."
    ),
    lifespan=lifespan,
)


LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Text Utils API</title>
    <style>
      :root {
        --bg: #f4efe7;
        --panel: rgba(255, 252, 247, 0.88);
        --text: #1f1d1a;
        --muted: #625b52;
        --accent: #b64d2f;
        --accent-2: #1f6f78;
        --border: rgba(31, 29, 26, 0.12);
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(182, 77, 47, 0.16), transparent 30%),
          radial-gradient(circle at bottom right, rgba(31, 111, 120, 0.16), transparent 35%),
          linear-gradient(135deg, #efe2d0, var(--bg));
      }
      main {
        max-width: 960px;
        margin: 0 auto;
        min-height: 100vh;
        padding: 48px 20px 56px;
        display: grid;
        gap: 20px;
      }
      .hero, .card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 20px;
        backdrop-filter: blur(8px);
        box-shadow: 0 16px 50px rgba(48, 36, 24, 0.08);
      }
      .hero {
        padding: 28px;
      }
      .eyebrow {
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent-2);
        font-size: 0.78rem;
        margin-bottom: 12px;
      }
      h1 {
        margin: 0 0 10px;
        font-size: clamp(2.4rem, 6vw, 4.8rem);
        line-height: 0.95;
      }
      p {
        margin: 0;
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.6;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 22px;
      }
      .button {
        display: inline-block;
        padding: 12px 18px;
        border-radius: 999px;
        text-decoration: none;
        color: white;
        background: var(--accent);
        font-weight: 700;
      }
      .button.secondary {
        background: var(--accent-2);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }
      .card {
        padding: 18px;
      }
      h2 {
        margin: 0 0 6px;
        font-size: 1.1rem;
      }
      code {
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.92rem;
        color: var(--accent-2);
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <div class="eyebrow">Text Utils API</div>
        <h1>Text transforms, stats, and formatting in one place.</h1>
        <p>
          Use authenticated JSON endpoints for tiny unicode text, zalgo output, slug generation,
          text statistics, and case conversion. Interactive API docs are available below.
        </p>
        <div class="actions">
          <a class="button" href="/docs">Open Swagger Docs</a>
          <a class="button secondary" href="/redoc">Open ReDoc</a>
        </div>
      </section>
      <section class="grid">
        <article class="card">
          <h2><code>POST /v1/tiny-text</code></h2>
          <p>Generate unicode tiny-text variants with superscript, small caps, and subscript output.</p>
        </article>
        <article class="card">
          <h2><code>POST /v1/zalgo-text</code></h2>
          <p>Add deterministic combining marks for glitch-style text with configurable intensity.</p>
        </article>
        <article class="card">
          <h2><code>POST /v1/slugify</code></h2>
          <p>Create URL-safe slugs with custom separators, optional case preservation, and length caps.</p>
        </article>
        <article class="card">
          <h2><code>POST /v1/text-stats</code></h2>
          <p>Return word, sentence, line, and character counts plus an estimated reading time.</p>
        </article>
        <article class="card">
          <h2><code>POST /v1/case-convert</code></h2>
          <p>Convert text into snake, kebab, camel, pascal, sentence, title, and constant variants.</p>
        </article>
        <article class="card">
          <h2><code>GET /healthz</code></h2>
          <p>Simple unauthenticated health check for deployments, load balancers, and uptime checks.</p>
        </article>
      </section>
    </main>
  </body>
</html>
"""


class TinyTextRequest(BaseModel):
    text: str = Field(..., description="Text to convert into tiny unicode text.")
    mode: TinyTextMode = Field(
        default=TinyTextMode.SUPERSCRIPT,
        description="Output style to use for the primary tiny_text field.",
    )


class TinyTextResponse(BaseModel):
    input_text: str
    mode: TinyTextMode
    tiny_text: str
    variants: dict[str, str]


class ZalgoTextRequest(BaseModel):
    text: str = Field(..., description="Text to convert into zalgo text.")
    intensity: int = Field(default=1, ge=0, le=3)
    direction: ZalgoDirection = Field(default=ZalgoDirection.ALL)


class ZalgoTextResponse(BaseModel):
    input_text: str
    intensity: int
    direction: ZalgoDirection
    output_text: str


class SlugifyRequest(BaseModel):
    text: str = Field(..., description="Text to convert into a URL slug.")
    separator: str = Field(default="-", min_length=1, max_length=1)
    lowercase: bool = True
    max_length: int | None = Field(default=None, ge=1)


class SlugifyResponse(BaseModel):
    input_text: str
    output_text: str
    separator: str
    lowercase: bool
    variants: dict[str, str]


class TextStatsRequest(BaseModel):
    text: str = Field(..., description="Text to analyze.")


class TextStatsResponse(BaseModel):
    input_text: str
    stats: dict[str, float | int]


class CaseConvertRequest(BaseModel):
    text: str = Field(..., description="Text to convert between case styles.")
    mode: CaseMode = Field(default=CaseMode.SNAKE)


class CaseConvertResponse(BaseModel):
    input_text: str
    mode: CaseMode
    output_text: str
    variants: dict[str, str]


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page() -> HTMLResponse:
    return HTMLResponse(content=LANDING_PAGE)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/tiny-text", response_model=TinyTextResponse)
def create_tiny_text(
    payload: TinyTextRequest,
    _: str = Depends(require_api_key),
) -> TinyTextResponse:
    variants = all_variants(payload.text)
    return TinyTextResponse(
        input_text=payload.text,
        mode=payload.mode,
        tiny_text=variants[payload.mode.value],
        variants=variants,
    )


@app.post("/v1/zalgo-text", response_model=ZalgoTextResponse)
def create_zalgo_text(
    payload: ZalgoTextRequest,
    _: str = Depends(require_api_key),
) -> ZalgoTextResponse:
    return ZalgoTextResponse(
        input_text=payload.text,
        intensity=payload.intensity,
        direction=payload.direction,
        output_text=zalgo_text(payload.text, payload.intensity, payload.direction),
    )


@app.post("/v1/slugify", response_model=SlugifyResponse)
def create_slug(
    payload: SlugifyRequest,
    _: str = Depends(require_api_key),
) -> SlugifyResponse:
    variants = {
        "kebab": slugify_text(payload.text, separator="-", lowercase=True, max_length=payload.max_length),
        "snake": slugify_text(payload.text, separator="_", lowercase=True, max_length=payload.max_length),
    }
    return SlugifyResponse(
        input_text=payload.text,
        output_text=slugify_text(
            payload.text,
            separator=payload.separator,
            lowercase=payload.lowercase,
            max_length=payload.max_length,
        ),
        separator=payload.separator,
        lowercase=payload.lowercase,
        variants=variants,
    )


@app.post("/v1/text-stats", response_model=TextStatsResponse)
def create_text_stats(
    payload: TextStatsRequest,
    _: str = Depends(require_api_key),
) -> TextStatsResponse:
    return TextStatsResponse(
        input_text=payload.text,
        stats=text_stats(payload.text),
    )


@app.post("/v1/case-convert", response_model=CaseConvertResponse)
def create_case_convert(
    payload: CaseConvertRequest,
    _: str = Depends(require_api_key),
) -> CaseConvertResponse:
    variants = case_variants(payload.text)
    return CaseConvertResponse(
        input_text=payload.text,
        mode=payload.mode,
        output_text=variants[payload.mode.value],
        variants=variants,
    )
