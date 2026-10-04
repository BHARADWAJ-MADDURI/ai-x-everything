from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from socket import timeout as SocketTimeout
import ssl
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from src.discovery.urls import is_safe_public_http_url


class RetrievalStatus(Enum):
    SUCCESS = "success"
    UNSAFE_URL = "unsafe_url"
    HTTP_ERROR = "http_error"
    TIMEOUT = "timeout"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    TOO_LARGE = "too_large"
    ERROR = "error"


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    final_url: str
    content_type: str
    body: bytes


@dataclass(frozen=True)
class RetrievedSource:
    source_url: str
    final_url: str | None
    status_code: int | None
    content_type: str | None
    retrieved_at: datetime
    title: str | None
    raw_text: str
    retrieval_status: RetrievalStatus
    error: str | None = None


Transport = Callable[[str, float, int, str], HttpResponse]


class SourceRetriever:
    """Retrieve public HTTP/HTTPS source material with bounded, injectable I/O."""

    def __init__(
        self,
        *,
        transport: Transport | None = None,
        timeout_seconds: float = 10.0,
        max_response_bytes: int = 750_000,
        user_agent: str = "Everything-x-AI/0.1 research",
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.transport = transport or default_http_transport
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def retrieve(self, url: str) -> RetrievedSource:
        retrieved_at = self.clock()
        if not is_safe_public_http_url(url):
            return _failure(url, retrieved_at, RetrievalStatus.UNSAFE_URL, "unsafe or unsupported URL")
        try:
            response = self.transport(url, self.timeout_seconds, self.max_response_bytes, self.user_agent)
        except TimeoutError:
            return _failure(url, retrieved_at, RetrievalStatus.TIMEOUT, "request timed out")
        except ValueError as exc:
            return _failure(url, retrieved_at, RetrievalStatus.UNSAFE_URL, str(exc))
        except HTTPError as exc:
            return RetrievedSource(
                source_url=url,
                final_url=getattr(exc, "url", url),
                status_code=exc.code,
                content_type=None,
                retrieved_at=retrieved_at,
                title=None,
                raw_text="",
                retrieval_status=RetrievalStatus.HTTP_ERROR,
                error=f"HTTP {exc.code}",
            )
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, SocketTimeout):
                return _failure(url, retrieved_at, RetrievalStatus.TIMEOUT, "request timed out")
            return _failure(url, retrieved_at, RetrievalStatus.ERROR, str(reason))
        except Exception as exc:
            return _failure(url, retrieved_at, RetrievalStatus.ERROR, str(exc))

        if not is_safe_public_http_url(response.final_url):
            return _failure(url, retrieved_at, RetrievalStatus.UNSAFE_URL, "unsafe redirect destination")
        if response.status_code >= 400:
            return RetrievedSource(
                source_url=url,
                final_url=response.final_url,
                status_code=response.status_code,
                content_type=response.content_type,
                retrieved_at=retrieved_at,
                title=None,
                raw_text="",
                retrieval_status=RetrievalStatus.HTTP_ERROR,
                error=f"HTTP {response.status_code}",
            )
        if len(response.body) > self.max_response_bytes:
            return RetrievedSource(
                source_url=url,
                final_url=response.final_url,
                status_code=response.status_code,
                content_type=response.content_type,
                retrieved_at=retrieved_at,
                title=None,
                raw_text="",
                retrieval_status=RetrievalStatus.TOO_LARGE,
                error="response exceeded maximum size",
            )
        if not _supported_content_type(response.content_type):
            return RetrievedSource(
                source_url=url,
                final_url=response.final_url,
                status_code=response.status_code,
                content_type=response.content_type,
                retrieved_at=retrieved_at,
                title=None,
                raw_text="",
                retrieval_status=RetrievalStatus.UNSUPPORTED_CONTENT_TYPE,
                error="unsupported content type",
            )
        text = response.body.decode(_charset(response.content_type), errors="replace")
        return RetrievedSource(
            source_url=url,
            final_url=response.final_url,
            status_code=response.status_code,
            content_type=response.content_type,
            retrieved_at=retrieved_at,
            title=None,
            raw_text=text,
            retrieval_status=RetrievalStatus.SUCCESS,
            error=None,
        )


def default_http_transport(
    url: str,
    timeout_seconds: float,
    max_response_bytes: int,
    user_agent: str,
) -> HttpResponse:
    opener = build_opener(_SafeRedirectHandler, HTTPSHandler(context=_ssl_context()))
    request = Request(url, headers={"User-Agent": user_agent})
    with opener.open(request, timeout=timeout_seconds) as response:
        body = response.read(max_response_bytes + 1)
        return HttpResponse(
            status_code=response.status,
            final_url=response.geturl(),
            content_type=response.headers.get("Content-Type", ""),
            body=body,
        )


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        if not is_safe_public_http_url(newurl):
            raise ValueError("unsafe redirect destination")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _supported_content_type(content_type: str) -> bool:
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type in {"text/html", "application/xhtml+xml", "text/plain"}


def _ssl_context() -> ssl.SSLContext:
    cafile = Path("/etc/ssl/cert.pem")
    if cafile.exists():
        return ssl.create_default_context(cafile=str(cafile))
    return ssl.create_default_context()


def _charset(content_type: str) -> str:
    for part in content_type.split(";"):
        key, _, value = part.strip().partition("=")
        if key.lower() == "charset" and value:
            return value
    return "utf-8"


def _failure(
    url: str,
    retrieved_at: datetime,
    status: RetrievalStatus,
    error: str,
) -> RetrievedSource:
    return RetrievedSource(
        source_url=url,
        final_url=None,
        status_code=None,
        content_type=None,
        retrieved_at=retrieved_at,
        title=None,
        raw_text="",
        retrieval_status=status,
        error=error,
    )
