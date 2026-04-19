from contextlib import asynccontextmanager
from html import escape

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse, Response
from markdown import markdown as render_markdown
from pydantic import BaseModel, Field

from app.auth import require_api_key
from app.config import get_settings
from app.images import generate_placeholder_image
from app.shares import ShareAlreadyExistsError, create_share, get_share, init_share_db
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
    init_share_db(settings.share_db_path)
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
          text statistics, case conversion, and configurable test image generation. Interactive API docs are available below.
        </p>
        <div class="actions">
          <a class="button secondary" href="/share">Open Share Editor</a>
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
          <h2><code>GET /v1/test-image</code></h2>
          <p>Generate a configurable placeholder PNG with custom size, text, and foreground/background colors.</p>
        </article>
        <article class="card">
          <h2><code>POST /v1/share</code></h2>
          <p>Create persistent markdown shares that load publicly at <code>/share/{slug}</code>.</p>
        </article>
        <article class="card">
          <h2><code>GET /share</code></h2>
          <p>Pastebin-style markdown editor for creating and copying shareable links.</p>
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


class ShareRequest(BaseModel):
    slug: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Lowercase URL slug used in /share/{slug}.",
    )
    markdown: str = Field(..., min_length=1, max_length=200_000)
    title: str | None = Field(default=None, max_length=120)


class ShareResponse(BaseModel):
    slug: str
    title: str
    markdown: str
    created_at: str
    share_url: str


def _share_url(slug: str) -> str:
    return f"{get_settings().share_base_url}/share/{slug}"


def _share_db_path() -> str:
    settings = get_settings()
    init_share_db(settings.share_db_path)
    return settings.share_db_path


def _share_title(title: str | None, slug: str) -> str:
    return title.strip() if title and title.strip() else slug


def _render_share_markdown(markdown_text: str) -> str:
    safe_markdown = escape(markdown_text)
    return render_markdown(
        safe_markdown,
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
    )


SHARE_EDITOR_PAGE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Create Share | Text Utils API</title>
    <style>
      :root {
        --bg: #0f1417;
        --panel: #172026;
        --panel-2: #1f2b33;
        --text: #f5f1ea;
        --muted: #aeb8bf;
        --accent: #ff7a45;
        --accent-2: #69b6c1;
        --border: rgba(255, 255, 255, 0.08);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Consolas, "Courier New", monospace;
        background:
          radial-gradient(circle at top left, rgba(255, 122, 69, 0.16), transparent 28%),
          radial-gradient(circle at bottom right, rgba(105, 182, 193, 0.16), transparent 30%),
          linear-gradient(180deg, #11181d, var(--bg));
        color: var(--text);
      }
      main {
        max-width: 1280px;
        margin: 0 auto;
        min-height: 100vh;
        padding: 28px 18px;
        display: grid;
        gap: 18px;
      }
      .shell {
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 18px;
      }
      .panel {
        background: linear-gradient(180deg, rgba(31, 43, 51, 0.96), rgba(23, 32, 38, 0.96));
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.24);
      }
      .hero h1 {
        margin: 0 0 10px;
        font-size: clamp(2rem, 4vw, 3.8rem);
        line-height: 0.95;
      }
      .hero p, .hint, .status {
        color: var(--muted);
        line-height: 1.6;
      }
      .toolbar, .form-grid {
        display: grid;
        gap: 12px;
      }
      .form-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      label {
        display: grid;
        gap: 8px;
        font-size: 0.86rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--muted);
      }
      input, textarea, button {
        width: 100%;
        border: 1px solid var(--border);
        border-radius: 12px;
        background: rgba(8, 11, 13, 0.35);
        color: var(--text);
        padding: 12px 14px;
        font: inherit;
      }
      textarea {
        min-height: 420px;
        resize: vertical;
      }
      button {
        background: var(--accent);
        color: #180d07;
        font-weight: 700;
        cursor: pointer;
      }
      a {
        color: var(--accent-2);
      }
      code {
        color: var(--accent-2);
      }
      .linkbox {
        display: none;
        margin-top: 14px;
        padding: 12px 14px;
        border-radius: 12px;
        background: rgba(105, 182, 193, 0.08);
        border: 1px solid rgba(105, 182, 193, 0.25);
        word-break: break-all;
      }
      @media (max-width: 980px) {
        .shell, .form-grid {
          grid-template-columns: 1fr;
        }
        textarea {
          min-height: 320px;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="panel hero">
        <p class="hint">Markdown Share</p>
        <h1>Paste, choose a slug, and publish a link.</h1>
        <p>Created shares become public pages at <code>https://tiny.vk2fgav.com/share/{slug}</code>. The editor uses the protected API, so enter an API key once and the browser will remember it locally.</p>
      </section>
      <section class="shell">
        <section class="panel">
          <div class="toolbar">
            <div class="form-grid">
              <label>
                API Key
                <input id="api-key" type="password" placeholder="dev-key-change-me" />
              </label>
              <label>
                Slug
                <input id="slug" type="text" placeholder="example" />
              </label>
              <label>
                Title
                <input id="title" type="text" placeholder="Example share" />
              </label>
            </div>
            <label>
              Markdown
              <textarea id="markdown" placeholder="# Hello&#10;&#10;Write your markdown here..."></textarea>
            </label>
            <button id="publish" type="button">Publish Share</button>
            <div class="status" id="status">Ready.</div>
            <div class="linkbox" id="linkbox"></div>
          </div>
        </section>
        <section class="panel">
          <p class="hint">How it works</p>
          <p>1. Enter your API key.</p>
          <p>2. Pick a lowercase slug such as <code>release-notes</code>.</p>
          <p>3. Paste markdown and publish.</p>
          <p>The API response returns the final share URL, and the public page renders the stored markdown server-side.</p>
          <p><a href="/docs">Open API docs</a></p>
        </section>
      </section>
    </main>
    <script>
      const apiKeyInput = document.getElementById("api-key");
      const slugInput = document.getElementById("slug");
      const titleInput = document.getElementById("title");
      const markdownInput = document.getElementById("markdown");
      const publishButton = document.getElementById("publish");
      const statusEl = document.getElementById("status");
      const linkBox = document.getElementById("linkbox");
      const storageKey = "text-utils-api-key";

      apiKeyInput.value = localStorage.getItem(storageKey) || "";

      publishButton.addEventListener("click", async () => {
        const apiKey = apiKeyInput.value.trim();
        const slug = slugInput.value.trim();
        const title = titleInput.value.trim();
        const markdown = markdownInput.value;

        if (!apiKey || !slug || !markdown.trim()) {
          statusEl.textContent = "API key, slug, and markdown are required.";
          return;
        }

        localStorage.setItem(storageKey, apiKey);
        publishButton.disabled = true;
        statusEl.textContent = "Publishing...";
        linkBox.style.display = "none";
        linkBox.textContent = "";

        try {
          const response = await fetch("/v1/share", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-API-Key": apiKey
            },
            body: JSON.stringify({ slug, title, markdown })
          });

          const data = await response.json();
          if (!response.ok) {
            statusEl.textContent = data.detail || "Unable to publish share.";
            return;
          }

          statusEl.textContent = "Share created.";
          linkBox.style.display = "block";
          linkBox.innerHTML = '<a href="' + data.share_url + '">' + data.share_url + "</a>";
        } catch (error) {
          statusEl.textContent = "Network error while publishing share.";
        } finally {
          publishButton.disabled = false;
        }
      });
    </script>
  </body>
</html>
"""


SHARE_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <style>
      :root {{
        --bg: #f7f4ee;
        --paper: rgba(255, 255, 255, 0.88);
        --text: #1f1d1a;
        --muted: #6d6458;
        --border: rgba(31, 29, 26, 0.12);
        --accent: #b64d2f;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(182, 77, 47, 0.16), transparent 28%),
          linear-gradient(180deg, #efe7db, var(--bg));
      }}
      main {{
        max-width: 920px;
        margin: 0 auto;
        min-height: 100vh;
        padding: 28px 18px 56px;
      }}
      .panel {{
        background: var(--paper);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 22px;
        box-shadow: 0 16px 48px rgba(42, 33, 23, 0.08);
      }}
      .meta {{
        margin-bottom: 22px;
      }}
      .eyebrow {{
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.76rem;
        margin-bottom: 10px;
      }}
      h1 {{
        margin: 0 0 8px;
        font-size: clamp(2rem, 4vw, 3.6rem);
        line-height: 0.95;
      }}
      .sub {{
        color: var(--muted);
      }}
      article {{
        line-height: 1.75;
        font-size: 1.06rem;
      }}
      article pre {{
        overflow-x: auto;
        padding: 14px;
        border-radius: 12px;
        background: #1b2227;
        color: #f8f4ed;
      }}
      article code {{
        font-family: Consolas, "Courier New", monospace;
      }}
      article :not(pre) > code {{
        padding: 0.1em 0.35em;
        border-radius: 6px;
        background: rgba(31, 29, 26, 0.06);
      }}
      article blockquote {{
        margin: 1.2rem 0;
        padding: 0.2rem 1rem;
        border-left: 4px solid rgba(182, 77, 47, 0.35);
        color: var(--muted);
      }}
      article table {{
        width: 100%;
        border-collapse: collapse;
      }}
      article th, article td {{
        padding: 10px;
        border: 1px solid rgba(31, 29, 26, 0.1);
      }}
      a {{
        color: var(--accent);
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <div class="meta">
          <div class="eyebrow">Markdown Share</div>
          <h1>{title}</h1>
          <div class="sub">/{slug} · created {created_at}</div>
        </div>
        <article>{html}</article>
      </section>
    </main>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page() -> HTMLResponse:
    return HTMLResponse(content=LANDING_PAGE)


@app.get("/share", response_class=HTMLResponse, include_in_schema=False)
def share_editor_page() -> HTMLResponse:
    return HTMLResponse(content=SHARE_EDITOR_PAGE)


@app.get("/share/{slug}", response_class=HTMLResponse, include_in_schema=False)
def shared_markdown_page(slug: str) -> HTMLResponse:
    share = get_share(_share_db_path(), slug)
    if share is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found.")

    return HTMLResponse(
        content=SHARE_PAGE_TEMPLATE.format(
            title=escape(share.title),
            slug=escape(share.slug),
            created_at=escape(share.created_at),
            html=_render_share_markdown(share.markdown),
        )
    )


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/v1/test-image",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
def create_test_image(
    width: int = Query(default=600, ge=1, le=4000),
    height: int = Query(default=400, ge=1, le=4000),
    text: str = Query(default=""),
    bg: str = Query(default="dddddd"),
    fg: str = Query(default="222222"),
    _: str = Depends(require_api_key),
) -> Response:
    return Response(
        content=generate_placeholder_image(
            width=width,
            height=height,
            text=text,
            background=bg,
            foreground=fg,
        ),
        media_type="image/png",
    )


@app.post("/v1/share", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def create_markdown_share(
    payload: ShareRequest,
    _: str = Depends(require_api_key),
) -> ShareResponse:
    try:
        share = create_share(
            _share_db_path(),
            slug=payload.slug,
            title=_share_title(payload.title, payload.slug),
            markdown=payload.markdown,
        )
    except ShareAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slug '{exc.args[0]}' already exists.",
        ) from exc

    return ShareResponse(
        slug=share.slug,
        title=share.title,
        markdown=share.markdown,
        created_at=share.created_at,
        share_url=_share_url(share.slug),
    )


@app.get("/v1/share/{slug}", response_model=ShareResponse)
def get_markdown_share(slug: str) -> ShareResponse:
    share = get_share(_share_db_path(), slug)
    if share is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found.")

    return ShareResponse(
        slug=share.slug,
        title=share.title,
        markdown=share.markdown,
        created_at=share.created_at,
        share_url=_share_url(share.slug),
    )


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
