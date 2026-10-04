from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import ipaddress
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, UnidentifiedImageError

from src.rendering.carousel.models import (
    CropStrategy,
    FocalPoint,
    MediaAsset,
    MediaAssetType,
    MediaCandidate,
    MediaRightsStatus,
    MediaSourceType,
    VisualRole,
)


SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
APPROVED_RIGHTS = {MediaRightsStatus.APPROVED, MediaRightsStatus.ATTRIBUTION_REQUIRED}


class MediaSearchProvider(Protocol):
    def search(self, query: str, *, limit: int = 3) -> list[MediaCandidate]:
        """Return unselected candidate media for human review."""


class PexelsMediaProvider:
    """Small optional provider wrapper; never used by tests or deterministic demos."""

    endpoint = "https://api.pexels.com/v1/search"

    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    def search(self, query: str, *, limit: int = 3) -> list[MediaCandidate]:
        if not self.api_key:
            return []
        if limit < 1:
            return []
        # A future live smoke script can call this. Unit tests keep this path unused.
        raise NotImplementedError("Pexels live search is intentionally not part of deterministic rendering")


def visual_role_for_story(*, domain: str, has_media: bool = False, has_numeric_claim: bool = False) -> VisualRole:
    normalized = domain.lower()
    if has_media and any(token in normalized for token in ("robot", "health", "hardware", "chip")):
        return VisualRole.SOURCE_MEDIA
    if any(token in normalized for token in ("research", "model", "science")):
        return VisualRole.EXPLAINER_DIAGRAM
    if has_numeric_claim or any(token in normalized for token in ("chip", "infrastructure")):
        return VisualRole.EDITORIAL_GRAPHIC
    if any(token in normalized for token in ("policy", "workforce", "regulation")):
        return VisualRole.TYPOGRAPHY
    return VisualRole.TYPOGRAPHY


def media_search_query(subject: str, domain: str, verified_entities: list[str]) -> str:
    parts = [subject, domain, *verified_entities]
    return " ".join(part.strip() for part in parts if part.strip())


def cap_candidates(candidates: list[MediaCandidate], limit: int = 3) -> list[MediaCandidate]:
    return sorted(candidates, key=lambda candidate: candidate.rank)[:limit]


def preserve_human_selection(selection_asset_id: str, candidates: list[MediaCandidate]) -> MediaCandidate | None:
    for candidate in candidates:
        if candidate.asset.asset_id == selection_asset_id:
            return candidate
    return None


def validate_media_asset(asset: MediaAsset) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if asset.license_status not in APPROVED_RIGHTS:
        issues.append(f"rights {asset.license_status.value} blocked")
    if asset.license_status is MediaRightsStatus.ATTRIBUTION_REQUIRED and not asset.attribution_text:
        issues.append("attribution-required media is missing attribution text")
    if asset.local_path is None:
        issues.append("media asset is missing local path")
    elif not asset.local_path.exists():
        issues.append("media asset local path does not exist")
    if asset.width <= 0 or asset.height <= 0:
        issues.append("media asset has invalid dimensions")
    return not issues, issues


def is_safe_media_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.hostname
    if not host:
        return False
    if host == "localhost" or host.endswith(".localhost"):
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)


class MediaDownloadError(ValueError):
    pass


class MediaCache:
    def __init__(
        self,
        root: Path,
        *,
        max_bytes: int = 5_000_000,
        min_width: int = 640,
        min_height: int = 360,
        transport=None,
    ) -> None:
        self.root = root
        self.max_bytes = max_bytes
        self.min_width = min_width
        self.min_height = min_height
        self.transport = transport or _default_transport

    def fetch_original(self, asset: MediaAsset) -> MediaAsset:
        if not is_safe_media_url(asset.original_url):
            raise MediaDownloadError("unsafe media URL")
        cache_dir = self.root / asset.story_id / _stable_key(asset.original_url)
        original_path = cache_dir / f"original{_extension_for_mime(asset.mime_type)}"
        if original_path.exists():
            width, height, mime_type = _inspect_image(original_path)
            return replace(asset, local_path=original_path, width=width, height=height, mime_type=mime_type)

        body, content_type = self.transport(asset.original_url, self.max_bytes)
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type not in SUPPORTED_IMAGE_TYPES:
            raise MediaDownloadError("unsupported content type")
        if len(body) > self.max_bytes:
            raise MediaDownloadError("oversized download")
        cache_dir.mkdir(parents=True, exist_ok=True)
        original_path.write_bytes(body)
        width, height, mime_type = _inspect_image(original_path)
        if width < self.min_width or height < self.min_height:
            raise MediaDownloadError("image below minimum resolution")
        return replace(
            asset,
            local_path=original_path,
            mime_type=mime_type,
            width=width,
            height=height,
            retrieved_at=datetime.now(timezone.utc),
        )

    def normalize(self, asset: MediaAsset, *, width: int, height: int) -> Path:
        if asset.local_path is None:
            raise MediaDownloadError("missing original media")
        if asset.width < width * 0.5 or asset.height < height * 0.5:
            raise MediaDownloadError("extreme upscale blocked")
        derivative_dir = self.root / asset.story_id / asset.asset_id
        derivative_dir.mkdir(parents=True, exist_ok=True)
        derivative_path = derivative_dir / f"{asset.crop_strategy.value}_{width}x{height}.jpg"
        if derivative_path.exists():
            return derivative_path
        with Image.open(asset.local_path) as image:
            image = image.convert("RGB")
            normalized = normalize_image(
                image,
                target_size=(width, height),
                crop_strategy=asset.crop_strategy,
                focal_point=asset.focal_point,
            )
            normalized.save(derivative_path, quality=92)
        return derivative_path


def normalize_image(
    image: Image.Image,
    *,
    target_size: tuple[int, int],
    crop_strategy: CropStrategy,
    focal_point: FocalPoint = FocalPoint(),
) -> Image.Image:
    target_width, target_height = target_size
    if crop_strategy is CropStrategy.CONTAIN:
        contained = Image.new("RGB", target_size, (244, 241, 234))
        copy = image.copy()
        copy.thumbnail(target_size, Image.Resampling.LANCZOS)
        contained.paste(copy, ((target_width - copy.width) // 2, (target_height - copy.height) // 2))
        return contained

    scale = max(target_width / image.width, target_height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = _crop_left(resized.width, target_width, crop_strategy, focal_point.x)
    top = _crop_top(resized.height, target_height, crop_strategy, focal_point.y)
    return resized.crop((left, top, left + target_width, top + target_height))


def _crop_left(width: int, target: int, crop_strategy: CropStrategy, focal_x: float) -> int:
    if crop_strategy is CropStrategy.LEFT:
        return 0
    if crop_strategy is CropStrategy.RIGHT:
        return max(0, width - target)
    if crop_strategy is CropStrategy.CENTER:
        return max(0, min(width - target, round(width * focal_x - target / 2)))
    return max(0, (width - target) // 2)


def _crop_top(height: int, target: int, crop_strategy: CropStrategy, focal_y: float) -> int:
    if crop_strategy is CropStrategy.TOP:
        return 0
    if crop_strategy is CropStrategy.BOTTOM:
        return max(0, height - target)
    if crop_strategy is CropStrategy.CENTER:
        return max(0, min(height - target, round(height * focal_y - target / 2)))
    return max(0, (height - target) // 2)


def _inspect_image(path: Path) -> tuple[int, int, str]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.width, image.height, Image.MIME.get(image.format, "")
    except (UnidentifiedImageError, OSError) as exc:
        raise MediaDownloadError("malformed image") from exc


def _default_transport(url: str, max_bytes: int) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "Everything x AI media acquisition/0.1"})
    with urlopen(request, timeout=10) as response:
        body = response.read(max_bytes + 1)
        return body, response.headers.get("Content-Type", "")


def _stable_key(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]


def _extension_for_mime(mime_type: str) -> str:
    media_type = mime_type.split(";", 1)[0].strip().lower()
    return { "image/png": ".png", "image/webp": ".webp" }.get(media_type, ".jpg")
