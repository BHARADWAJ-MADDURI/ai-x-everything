from dataclasses import dataclass, field
from datetime import datetime
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


class VisualRole(Enum):
    SOURCE_MEDIA = "source_media"
    LICENSED_MEDIA = "licensed_media"
    EXPLAINER_DIAGRAM = "explainer_diagram"
    EDITORIAL_GRAPHIC = "editorial_graphic"
    TYPOGRAPHY = "typography"


class MediaAssetType(Enum):
    IMAGE = "image"


class MediaSourceType(Enum):
    OFFICIAL_SOURCE = "official_source"
    LICENSED_PROVIDER = "licensed_provider"
    LOCAL_DEMO = "local_demo"


class MediaRightsStatus(Enum):
    APPROVED = "approved"
    ATTRIBUTION_REQUIRED = "attribution_required"
    UNKNOWN = "unknown"
    REJECTED = "rejected"


class CropStrategy(Enum):
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    CONTAIN = "contain"


class EditorialComposition(Enum):
    PHOTO_DOMINANT = "photo_dominant"
    TEXT_EDITORIAL = "text_editorial"
    DIAGRAM_EXPLAINER = "diagram_explainer"
    DATA_EDITORIAL = "data_editorial"
    DOCUMENT_POLICY = "document_policy"


@dataclass(frozen=True)
class FocalPoint:
    x: float = 0.5
    y: float = 0.5


@dataclass(frozen=True)
class MediaAsset:
    asset_id: str
    story_id: str
    asset_type: MediaAssetType
    source_type: MediaSourceType
    source_url: str
    original_url: str
    local_path: Path | None
    mime_type: str
    width: int
    height: int
    license_status: MediaRightsStatus
    license_name: str | None = None
    attribution_required: bool = False
    attribution_text: str | None = None
    retrieved_at: datetime | None = None
    crop_strategy: CropStrategy = CropStrategy.CENTER
    focal_point: FocalPoint = field(default_factory=FocalPoint)
    visual_role: VisualRole = VisualRole.TYPOGRAPHY


@dataclass(frozen=True)
class MediaCandidate:
    asset: MediaAsset
    relevance_note: str
    rank: int
    approved_for_render: bool = False


@dataclass(frozen=True)
class HumanVisualSelection:
    story_id: str
    visual_role: VisualRole
    selected_asset_id: str | None = None
    use_diagram: bool = False
    use_typography: bool = False


@dataclass(frozen=True)
class DiagramNode:
    node_id: str
    label: str
    supporting_claim_ids: list[str]


@dataclass(frozen=True)
class DiagramEdge:
    from_node: str
    to_node: str
    label: str
    supporting_claim_ids: list[str]


@dataclass(frozen=True)
class DiagramSpec:
    story_id: str
    nodes: list[DiagramNode]
    edges: list[DiagramEdge]
    supporting_claim_ids: list[str]


@dataclass(frozen=True)
class EditorialGraphicSpec:
    story_id: str
    graphic_type: str
    label: str
    value: str | None
    supporting_claim_ids: list[str]


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
    visual_role: VisualRole = VisualRole.TYPOGRAPHY
    media_asset: MediaAsset | None = None
    media_attribution: str | None = None
    layout_composition: EditorialComposition = EditorialComposition.TEXT_EDITORIAL
    diagram_spec: DiagramSpec | None = None
    graphic_spec: EditorialGraphicSpec | None = None
    teasers: list[str] = field(default_factory=list)
    text_regions: list[TextRegion] = field(default_factory=list)


@dataclass(frozen=True)
class RenderedCarousel:
    variant: CarouselVariant
    output_dir: Path
    slide_paths: list[Path]
    contact_sheet_path: Path
    qa_status: CarouselQAStatus
    qa_messages: list[str]
