from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from src.editorial.formats import AIBriefItem


class CarouselVariant(Enum):
    EDITORIAL = "editorial"
    DYNAMIC = "dynamic"


class CarouselSlideType(Enum):
    COVER = "cover"
    STORY = "story"
    OUTRO = "outro"


class CarouselQAStatus(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass(frozen=True)
class CarouselCanvasConfig:
    width: int = 1080
    height: int = 1350
    safe_left: int = 84
    safe_top: int = 90
    safe_right: int = 996
    safe_bottom: int = 1260

    @property
    def safe_width(self) -> int:
        return self.safe_right - self.safe_left

    @property
    def safe_height(self) -> int:
        return self.safe_bottom - self.safe_top


CANVAS = CarouselCanvasConfig()


@dataclass(frozen=True)
class TextRegion:
    name: str
    box: tuple[int, int, int, int]
    min_font_size: int
    text: str


@dataclass(frozen=True)
class CarouselSlide:
    position: int
    slide_type: CarouselSlideType
    variant: CarouselVariant
    title: str
    subtitle: str | None = None
    item: AIBriefItem | None = None
    category: str | None = None
    source_label: str | None = None
    text_regions: list[TextRegion] = field(default_factory=list)


@dataclass(frozen=True)
class RenderedCarousel:
    variant: CarouselVariant
    output_dir: Path
    slide_paths: list[Path]
    contact_sheet_path: Path
    qa_status: CarouselQAStatus
    qa_messages: list[str]
