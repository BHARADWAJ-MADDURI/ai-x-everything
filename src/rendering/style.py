from dataclasses import dataclass
from enum import Enum

from src.rendering.fonts import TypographyRole


class ContentStyle(Enum):
    """Visual art-direction style for the same canonical content."""

    DYNAMIC_TECH = "dynamic_tech"
    EDITORIAL_HUMAN = "editorial_human"


class EditorialTone(Enum):
    """Editorial tone input for deterministic style resolution."""

    NEUTRAL = "neutral"


@dataclass(frozen=True)
class SafeZone:
    """Shared mobile-safe bounds for vertical social layouts."""

    left: int = 96
    top: int = 150
    right: int = 984
    bottom: int = 1720

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class VisualStyle:
    """Resolved deterministic visual system for a rendered asset."""

    name: str
    background: tuple[int, int, int]
    surface: tuple[int, int, int]
    surface_alt: tuple[int, int, int]
    text: tuple[int, int, int]
    muted: tuple[int, int, int]
    accent: tuple[int, int, int]
    accent_alt: tuple[int, int, int]
    marker: tuple[int, int, int]
    grid: tuple[int, int, int]
    headline_role: TypographyRole
    body_role: TypographyRole
    mono_role: TypographyRole
    safe_zone: SafeZone = SafeZone()


class StyleResolver:
    """Deterministically maps domain/style/tone into a visual system."""

    def resolve(
        self,
        *,
        domain: str,
        content_style: ContentStyle,
        editorial_tone: EditorialTone,
    ) -> VisualStyle:
        if content_style is ContentStyle.DYNAMIC_TECH:
            return VisualStyle(
                name=f"{domain}:{content_style.value}:{editorial_tone.value}",
                background=(8, 15, 26),
                surface=(18, 31, 48),
                surface_alt=(19, 43, 54),
                text=(241, 247, 250),
                muted=(161, 181, 191),
                accent=(94, 221, 206),
                accent_alt=(255, 194, 87),
                marker=(99, 132, 255),
                grid=(37, 58, 78),
                headline_role=TypographyRole.CONDENSED_DISPLAY,
                body_role=TypographyRole.SANS,
                mono_role=TypographyRole.MONO,
            )

        return VisualStyle(
            name=f"{domain}:{content_style.value}:{editorial_tone.value}",
            background=(242, 238, 229),
            surface=(255, 252, 244),
            surface_alt=(229, 236, 231),
            text=(29, 34, 38),
            muted=(91, 99, 101),
            accent=(14, 104, 119),
            accent_alt=(169, 78, 58),
            marker=(232, 198, 87),
            grid=(205, 199, 187),
            headline_role=TypographyRole.EDITORIAL_SERIF,
            body_role=TypographyRole.SANS,
            mono_role=TypographyRole.MONO,
        )
