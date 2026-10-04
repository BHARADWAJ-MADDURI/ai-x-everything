from dataclasses import dataclass
from enum import Enum
from html import unescape
from html.parser import HTMLParser
import re


class ExtractionQuality(Enum):
    GOOD = "good"
    POOR = "poor"
    EMPTY = "empty"


@dataclass(frozen=True)
class ExtractedText:
    title: str | None
    text: str
    quality: ExtractionQuality


class ArticleTextExtractor:
    """Small deterministic HTML/text extractor for source evidence acquisition."""

    def extract(self, raw_text: str, content_type: str | None) -> ExtractedText:
        if not raw_text.strip():
            return ExtractedText(title=None, text="", quality=ExtractionQuality.EMPTY)
        media_type = (content_type or "").split(";", 1)[0].strip().lower()
        if media_type == "text/plain":
            text = _clean_text(raw_text)
            return ExtractedText(title=None, text=text, quality=_quality(text))
        parser = _ReadableHtmlParser()
        parser.feed(raw_text)
        text = _clean_text("\n".join(parser.blocks))
        return ExtractedText(title=parser.title, text=text, quality=_quality(text))


class _ReadableHtmlParser(HTMLParser):
    skip_tags = {"script", "style", "nav", "footer", "header", "aside", "form", "button", "svg", "noscript"}
    block_tags = {"p", "li", "blockquote", "h1", "h2", "h3", "h4", "article", "section"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._current: list[str] = []
        self._in_title = False
        self._title_parts: list[str] = []
        self.blocks: list[str] = []

    @property
    def title(self) -> str | None:
        title = _clean_text(" ".join(self._title_parts))
        return title or None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.skip_tags:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in self.skip_tags and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.block_tags:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
            return
        self._current.append(data)

    def _flush(self) -> None:
        text = _clean_text(" ".join(self._current))
        lowered = text.lower()
        if text and not (
            lowered.startswith("skip to content")
            or lowered.startswith("suggestions or feedback")
            or lowered.startswith("browse by topics")
            or "browse by topics" in lowered
            or "subscribe to mit news" in lowered
            or "press inquiries" in lowered
        ):
            self.blocks.append(text)
        self._current = []


def _quality(text: str) -> ExtractionQuality:
    if not text:
        return ExtractionQuality.EMPTY
    if len(text) < 240 or len(text.split()) < 35:
        return ExtractionQuality.POOR
    return ExtractionQuality.GOOD


def _clean_text(value: str) -> str:
    text = unescape(value)
    text = re.sub(r"\s+", " ", text)
    boilerplate = (
        "accept cookies",
        "sign up for our newsletter",
        "subscribe to continue",
        "advertisement",
    )
    lines = []
    for line in text.split("\n"):
        cleaned = line.strip()
        if cleaned and cleaned.lower() not in boilerplate:
            lines.append(cleaned)
    return " ".join(lines).strip()
