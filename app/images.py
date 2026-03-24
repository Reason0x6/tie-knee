from io import BytesIO

from PIL import Image, ImageColor, ImageDraw, ImageFont


def parse_color(value: str) -> tuple[int, int, int]:
    candidate = value.strip()
    if not candidate.startswith("#"):
        candidate = f"#{candidate}"
    return ImageColor.getrgb(candidate)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def generate_placeholder_image(
    width: int,
    height: int,
    text: str,
    background: str,
    foreground: str,
) -> bytes:
    image = Image.new("RGB", (width, height), color=parse_color(background))
    draw = ImageDraw.Draw(image)
    font = _load_font(max(14, min(width, height) // 6))
    display_text = text or f"{width}x{height}"

    bbox = draw.multiline_textbbox((0, 0), display_text, font=font, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    origin = ((width - text_width) / 2, (height - text_height) / 2)

    draw.multiline_text(
        origin,
        display_text,
        fill=parse_color(foreground),
        font=font,
        align="center",
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
