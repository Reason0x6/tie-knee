from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from app.auth import require_api_key
from app.config import get_settings
from app.tiny_text import TinyTextMode, all_variants, transform_text


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
