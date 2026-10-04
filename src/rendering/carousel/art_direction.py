from dataclasses import dataclass
from enum import Enum

from src.rendering.carousel.models import CarouselVariant
from src.rendering.fonts import TypographyRole


class BriefArtDirection(Enum):
    EDITORIAL_NEUTRAL = "editorial_neutral"
    TECHNICAL = "technical"
    RESEARCH = "research"
    CLINICAL = "clinical"
    INDUSTRIAL = "industrial"
    POLICY = "policy"


@dataclass(frozen=True)
class CarouselPalette:
    background: tuple[int, int, int]
    paper: tuple[int, int, int]
    ink: tuple[int, int, int]
    muted: tuple[int, int, int]
    accent: tuple[int, int, int]
    accent_alt: tuple[int, int, int]
    rule: tuple[int, int, int]
    grid: tuple[int, int, int]


@dataclass(frozen=True)
class CarouselArtStyle:
    direction: BriefArtDirection
    variant: CarouselVariant
    palette: CarouselPalette
    headline_role: TypographyRole
    body_role: TypographyRole
    label_role: TypographyRole
    motif: str


class BriefArtDirectionResolver:
    """Maps story semantics into bounded, publication-consistent treatments."""

    def resolve_direction(self, category: str | None, headline: str = "") -> BriefArtDirection:
        text = f"{category or ''} {headline}".lower()
        if any(term in text for term in ["policy", "regulation", "government", "workforce", "enterprise"]):
            return BriefArtDirection.POLICY
        if any(term in text for term in ["healthcare", "clinical", "biotech", "medical"]):
            return BriefArtDirection.CLINICAL
        if any(term in text for term in ["manufacturing", "robotics", "chips", "infrastructure", "hardware"]):
            return BriefArtDirection.INDUSTRIAL
        if any(term in text for term in ["research", "science", "model"]):
            return BriefArtDirection.RESEARCH
        if any(term in text for term in ["agent", "developer", "tool", "platform"]):
            return BriefArtDirection.TECHNICAL
        return BriefArtDirection.EDITORIAL_NEUTRAL

    def resolve_style(
        self,
        *,
        variant: CarouselVariant,
        category: str | None = None,
        headline: str = "",
    ) -> CarouselArtStyle:
        direction = self.resolve_direction(category, headline)
        if variant is CarouselVariant.DYNAMIC:
            return _dynamic_style(direction)
        return _editorial_style(direction)


def _editorial_style(direction: BriefArtDirection) -> CarouselArtStyle:
    accents = {
        BriefArtDirection.EDITORIAL_NEUTRAL: ((17, 96, 112), (175, 76, 55), "rule"),
        BriefArtDirection.TECHNICAL: ((35, 92, 150), (185, 110, 58), "diagram"),
        BriefArtDirection.RESEARCH: ((77, 88, 135), (169, 78, 58), "annotation"),
        BriefArtDirection.CLINICAL: ((24, 117, 112), (166, 91, 73), "index"),
        BriefArtDirection.INDUSTRIAL: ((42, 82, 118), (190, 126, 55), "grid"),
        BriefArtDirection.POLICY: ((74, 85, 94), (146, 75, 58), "column"),
    }
    accent, accent_alt, motif = accents[direction]
    return CarouselArtStyle(
        direction=direction,
        variant=CarouselVariant.EDITORIAL,
        palette=CarouselPalette(
            background=(239, 235, 226),
            paper=(255, 252, 244),
            ink=(27, 32, 35),
            muted=(86, 93, 95),
            accent=accent,
            accent_alt=accent_alt,
            rule=(199, 190, 176),
            grid=(222, 216, 205),
        ),
        headline_role=TypographyRole.EDITORIAL_SERIF,
        body_role=TypographyRole.SANS,
        label_role=TypographyRole.MONO,
        motif=motif,
    )


def _dynamic_style(direction: BriefArtDirection) -> CarouselArtStyle:
    accents = {
        BriefArtDirection.EDITORIAL_NEUTRAL: ((108, 224, 211), (255, 196, 89), "scanline"),
        BriefArtDirection.TECHNICAL: ((91, 181, 255), (118, 236, 209), "circuit"),
        BriefArtDirection.RESEARCH: ((167, 157, 255), (105, 220, 203), "matrix"),
        BriefArtDirection.CLINICAL: ((85, 218, 191), (242, 192, 111), "pulse"),
        BriefArtDirection.INDUSTRIAL: ((103, 164, 232), (247, 174, 79), "blueprint"),
        BriefArtDirection.POLICY: ((178, 193, 207), (255, 190, 112), "briefing"),
    }
    accent, accent_alt, motif = accents[direction]
    return CarouselArtStyle(
        direction=direction,
        variant=CarouselVariant.DYNAMIC,
        palette=CarouselPalette(
            background=(9, 16, 28),
            paper=(17, 29, 45),
            ink=(240, 247, 250),
            muted=(162, 181, 190),
            accent=accent,
            accent_alt=accent_alt,
            rule=(38, 58, 79),
            grid=(31, 48, 68),
        ),
        headline_role=TypographyRole.CONDENSED_DISPLAY,
        body_role=TypographyRole.SANS,
        label_role=TypographyRole.MONO,
        motif=motif,
    )
