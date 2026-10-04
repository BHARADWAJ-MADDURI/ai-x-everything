from src.editorial.formats import AIBriefPackage
from src.rendering.carousel.models import (
    CarouselSlide,
    CarouselSlideType,
    CarouselVariant,
    HumanVisualSelection,
    MediaAsset,
    VisualRole,
)


class AIBriefCarouselDirector:
    """Transforms a validated AI Brief into ordered slide models."""

    def build_slides(
        self,
        package: AIBriefPackage,
        variant: CarouselVariant,
        *,
        visual_selections: dict[str, HumanVisualSelection] | None = None,
        media_assets: dict[str, MediaAsset] | None = None,
    ) -> list[CarouselSlide]:
        visual_selections = visual_selections or {}
        media_assets = media_assets or {}
        slides = [
            CarouselSlide(
                position=1,
                slide_type=CarouselSlideType.COVER,
                variant=variant,
                title=package.title.upper(),
                subtitle=package.subtitle,
                teasers=[_teaser(item.headline) for item in package.items],
            )
        ]
        for item in package.items:
            source = item.source_refs[0] if item.source_refs else None
            selection = visual_selections.get(item.story_id)
            visual_role = selection.visual_role if selection else VisualRole.TYPOGRAPHY
            media_asset = media_assets.get(selection.selected_asset_id) if selection and selection.selected_asset_id else None
            slides.append(
                CarouselSlide(
                    position=item.position + 1,
                    slide_type=CarouselSlideType.STORY,
                    variant=variant,
                    title=item.headline,
                    subtitle=item.what_happened,
                    item=item,
                    category=item.category,
                    source_label=f"SOURCE · {source.source_name.upper()}" if source else None,
                    visual_role=visual_role,
                    media_asset=media_asset,
                    media_attribution=media_asset.attribution_text if media_asset and media_asset.attribution_required else None,
                )
            )
        slides.append(
            CarouselSlide(
                position=len(package.items) + 2,
                slide_type=CarouselSlideType.OUTRO,
                variant=variant,
                title="EVERYTHING × AI",
                subtitle="Understand what's changing.",
            )
        )
        return slides


def _teaser(headline: str, max_chars: int = 58) -> str:
    text = " ".join(headline.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"
