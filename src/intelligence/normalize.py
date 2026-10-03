import re
from dataclasses import replace
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.intelligence.models import CandidateItem


TRACKING_PREFIXES = ("utm_",)
TRACKING_KEYS = {"fbclid", "gclid"}


def clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(title: str) -> str:
    return clean_whitespace(title)


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or parts.path
    query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in TRACKING_KEYS and not key.startswith(TRACKING_PREFIXES)
    ]
    query = urlencode(query_items)
    return urlunsplit((scheme, netloc, path, query, ""))


def canonical_source_name(name: str) -> str:
    return clean_whitespace(name)


def normalize_candidate(candidate: CandidateItem) -> CandidateItem:
    """Normalize discovered candidate data without changing meaning."""

    summary = clean_whitespace(candidate.summary) if candidate.summary else None
    author = clean_whitespace(candidate.author) if candidate.author else None
    return replace(
        candidate,
        source_name=canonical_source_name(candidate.source_name),
        source_url=normalize_url(candidate.source_url),
        title=normalize_title(candidate.title),
        summary=summary or None,
        author=author or None,
    )


def title_tokens(title: str) -> set[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "for",
        "in",
        "new",
        "of",
        "on",
        "the",
        "to",
        "with",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", title.lower())
        if len(token) > 2 and token not in stop_words
    }
