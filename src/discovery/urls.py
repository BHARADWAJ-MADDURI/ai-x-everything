import ipaddress
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PREFIXES = ("utm_",)
TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def normalize_discovery_url(url: str) -> str:
    """Conservatively normalize URLs for traceable deduplication."""

    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    if parts.port:
        netloc = f"{hostname}:{parts.port}"
    else:
        netloc = hostname
    query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in TRACKING_KEYS and not key.lower().startswith(TRACKING_PREFIXES)
    ]
    return urlunsplit((scheme, netloc, parts.path or "/", urlencode(query_items), ""))


def is_safe_public_http_url(url: str) -> bool:
    """Reject schemes and hostnames/IPs that should never be fetched from user input."""

    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return False
    if parts.scheme.lower() not in {"http", "https"}:
        return False
    hostname = parts.hostname
    if not hostname:
        return False
    host = hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
    )
