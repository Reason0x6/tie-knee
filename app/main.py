from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
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
    title="Tiny Text API",
    version="1.0.0",
    description=(
        "Convert text into tiny unicode variants based on the LingoJam Tiny Text "
        "Generator mappings."
    ),
    lifespan=lifespan,
)


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
