import re
import unicodedata
from enum import StrEnum


class ZalgoDirection(StrEnum):
    UP = "up"
    MID = "mid"
    DOWN = "down"
    ALL = "all"


class CaseMode(StrEnum):
    LOWER = "lower"
    UPPER = "upper"
    TITLE = "title"
    SENTENCE = "sentence"
    SNAKE = "snake"
    KEBAB = "kebab"
    CAMEL = "camel"
    PASCAL = "pascal"
    CONSTANT = "constant"


ZALGO_UP = ["\u030d", "\u030e", "\u0304", "\u0305", "\u033f", "\u0311"]
ZALGO_MID = ["\u0315", "\u031b", "\u0340", "\u0341", "\u0358", "\u0321"]
ZALGO_DOWN = ["\u0316", "\u0317", "\u0318", "\u0319", "\u0323", "\u0324"]

WORD_RE = re.compile(r"[A-Za-z0-9]+")
NON_ALNUM_RE = re.compile(r"[^A-Za-z0-9]+")
SENTENCE_RE = re.compile(r"[.!?]+")


def zalgo_text(
    text: str,
    intensity: int = 1,
    direction: ZalgoDirection = ZalgoDirection.ALL,
) -> str:
    intensity = max(0, min(intensity, 3))
    if intensity == 0:
        return text

    pools: list[list[str]] = []
    if direction in (ZalgoDirection.UP, ZalgoDirection.ALL):
        pools.append(ZALGO_UP)
    if direction in (ZalgoDirection.MID, ZalgoDirection.ALL):
        pools.append(ZALGO_MID)
    if direction in (ZalgoDirection.DOWN, ZalgoDirection.ALL):
        pools.append(ZALGO_DOWN)

    transformed: list[str] = []
    visible_index = 0
    for char in text:
        transformed.append(char)
        if char.isspace():
            continue
        for pool in pools:
            for offset in range(intensity):
                transformed.append(pool[(visible_index + offset) % len(pool)])
        visible_index += 1

    return "".join(transformed)


def slugify_text(
    text: str,
    separator: str = "-",
    lowercase: bool = True,
    max_length: int | None = None,
) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    candidate = ascii_text.lower() if lowercase else ascii_text
    candidate = NON_ALNUM_RE.sub(separator, candidate)
    candidate = candidate.strip(separator)

    if max_length and max_length > 0:
        candidate = candidate[:max_length].strip(separator)

    return candidate


def text_stats(text: str) -> dict[str, float | int]:
    words = WORD_RE.findall(text)
    lines = text.count("\n") + 1 if text else 0
    sentences = len(SENTENCE_RE.findall(text))
    char_count = len(text)
    char_no_spaces = len(re.sub(r"\s+", "", text))
    reading_time_minutes = round(len(words) / 200, 2)

    return {
        "characters": char_count,
        "characters_no_spaces": char_no_spaces,
        "words": len(words),
        "lines": lines,
        "sentences": sentences,
        "reading_time_minutes": reading_time_minutes,
    }


def split_words(text: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    normalized = re.sub(r"[_\-\s]+", " ", normalized)
    return [word for word in WORD_RE.findall(normalized) if word]


def _sentence_case(words: list[str]) -> str:
    if not words:
        return ""

    lower_words = [word.lower() for word in words]
    lower_words[0] = lower_words[0].capitalize()
    return " ".join(lower_words)


def case_variants(text: str) -> dict[str, str]:
    words = split_words(text)
    lower_words = [word.lower() for word in words]
    title_words = [word.capitalize() for word in lower_words]

    return {
        CaseMode.LOWER.value: text.lower(),
        CaseMode.UPPER.value: text.upper(),
        CaseMode.TITLE.value: " ".join(title_words),
        CaseMode.SENTENCE.value: _sentence_case(words),
        CaseMode.SNAKE.value: "_".join(lower_words),
        CaseMode.KEBAB.value: "-".join(lower_words),
        CaseMode.CAMEL.value: "".join(
            [lower_words[0], *[word.capitalize() for word in lower_words[1:]]]
        )
        if lower_words
        else "",
        CaseMode.PASCAL.value: "".join(title_words),
        CaseMode.CONSTANT.value: "_".join(word.upper() for word in lower_words),
    }
