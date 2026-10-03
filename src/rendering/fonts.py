from enum import Enum
from pathlib import Path

from PIL import ImageFont


class TypographyRole(Enum):
    """Semantic font roles used by rendered media."""

    DISPLAY = "display"
    EDITORIAL_SERIF = "editorial_serif"
    SANS = "sans"
    MONO = "mono"
    CONDENSED_DISPLAY = "condensed_display"


FONT_FALLBACKS: dict[TypographyRole, list[str]] = {
    TypographyRole.DISPLAY: [
        "/System/Library/Fonts/Avenir Next.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
    TypographyRole.EDITORIAL_SERIF: [
        "/System/Library/Fonts/NewYork.ttf",
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Times.ttc",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ],
    TypographyRole.SANS: [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Avenir.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ],
    TypographyRole.MONO: [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
    ],
    TypographyRole.CONDENSED_DISPLAY: [
        "/System/Library/Fonts/Avenir Next Condensed.ttc",
        "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ],
}


class FontResolver:
    """Centralized resolver for system fonts with safe fallbacks."""

    def __init__(
        self,
        fallbacks: dict[TypographyRole, list[str]] | None = None,
    ) -> None:
        self.fallbacks = fallbacks or FONT_FALLBACKS

    def resolve_path(self, role: TypographyRole) -> Path | None:
        for candidate in self.fallbacks.get(role, []):
            path = Path(candidate)
            if path.exists():
                return path
        return None

    def font(self, role: TypographyRole, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        path = self.resolve_path(role)
        if path is None:
            return ImageFont.load_default(size=size)
        return ImageFont.truetype(str(path), size=size)
