from pathlib import Path

from PIL import Image

from src.editorial.formats import AIBriefPackage
from src.rendering.carousel.grounded_visuals import validate_diagram_spec, validate_editorial_graphic
from src.rendering.carousel.media import validate_media_asset
from src.rendering.carousel.models import (
    CANVAS,
    CarouselQAStatus,
    CarouselSlide,
    CarouselSlideType,
    TextRegion,
    VisualRole,
)


MIN_READABLE_FONT_SIZE = 18


def qa_slides(
    slides: list[CarouselSlide],
    package: AIBriefPackage,
    *,
    check_repeated_copy: bool = False,
) -> tuple[CarouselQAStatus, list[str]]:
    messages: list[str] = []
    status = CarouselQAStatus.PASS
    expected_count = package.item_count + 2
    if len(slides) != expected_count:
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append(f"slide count {len(slides)} did not match expected {expected_count}")
    positions = [slide.position for slide in slides]
    story_ids = [slide.item.story_id for slide in slides if slide.item is not None]
    if len(set(positions)) != len(positions):
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("duplicate slide position")
    if len(set(story_ids)) != len(story_ids):
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("duplicate story")
    cover = slides[0] if slides else None
    if cover is None or cover.slide_type is not CarouselSlideType.COVER or "AI BRIEF" not in cover.title:
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("cover missing AI Brief brand")
    if cover and (cover.subtitle or "") != package.subtitle:
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("cover count does not match actual Brief item count")
    if cover and cover.teasers and len(cover.teasers) != package.item_count:
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("cover teaser count does not match actual Brief item count")
    if cover:
        for teaser in cover.teasers:
            if len(teaser) > 70:
                status = _max_status(status, CarouselQAStatus.WARNING)
                messages.append("cover teaser may overflow")

    for slide in slides:
        if not slide.title.strip():
            status = _max_status(status, CarouselQAStatus.FAIL)
            messages.append(f"slide {slide.position} missing headline")
        if slide.slide_type is CarouselSlideType.STORY:
            if slide.item is None:
                status = _max_status(status, CarouselQAStatus.FAIL)
                messages.append(f"slide {slide.position} missing story item")
            if not slide.source_label:
                status = _max_status(status, CarouselQAStatus.FAIL)
                messages.append(f"slide {slide.position} missing source attribution")
            if check_repeated_copy and slide.item and _copy_repeats(slide):
                status = _max_status(status, CarouselQAStatus.WARNING)
                messages.append(f"slide {slide.position} repeats headline copy in body")
            media_status, media_messages = qa_slide_media(slide)
            status = _max_status(status, media_status)
            messages.extend(f"slide {slide.position}: {message}" for message in media_messages)
            grounded_status, grounded_messages = qa_grounded_visuals(slide)
            status = _max_status(status, grounded_status)
            messages.extend(f"slide {slide.position}: {message}" for message in grounded_messages)
        region_status, region_messages = qa_text_regions(slide.text_regions)
        status = _max_status(status, region_status)
        messages.extend(f"slide {slide.position}: {message}" for message in region_messages)
    return status, messages


def qa_slide_media(slide: CarouselSlide) -> tuple[CarouselQAStatus, list[str]]:
    if slide.visual_role not in {VisualRole.SOURCE_MEDIA, VisualRole.LICENSED_MEDIA}:
        return CarouselQAStatus.PASS, []
    messages: list[str] = []
    if slide.media_asset is None:
        return CarouselQAStatus.FAIL, ["media visual role is missing selected media"]
    allowed, issues = validate_media_asset(slide.media_asset)
    messages.extend(issues)
    if slide.media_asset.attribution_required and not slide.media_attribution:
        messages.append("required media attribution is missing")
    status = CarouselQAStatus.PASS if allowed and not messages else CarouselQAStatus.FAIL
    return status, messages


def qa_grounded_visuals(slide: CarouselSlide) -> tuple[CarouselQAStatus, list[str]]:
    if slide.item is None:
        return CarouselQAStatus.PASS, []
    verified_claim_ids = set(slide.item.supporting_claim_ids)
    status = CarouselQAStatus.PASS
    messages: list[str] = []
    if slide.diagram_spec:
        ok, issues = validate_diagram_spec(slide.diagram_spec, verified_claim_ids)
        if not ok:
            status = _max_status(status, CarouselQAStatus.FAIL)
            messages.extend(issues)
    if slide.graphic_spec:
        claim_text = " ".join([slide.item.headline, slide.item.what_happened, slide.item.why_it_matters])
        ok, issues = validate_editorial_graphic(slide.graphic_spec, claim_text)
        if not ok:
            status = _max_status(status, CarouselQAStatus.FAIL)
            messages.extend(issues)
    return status, messages


def qa_text_regions(regions: list[TextRegion]) -> tuple[CarouselQAStatus, list[str]]:
    status = CarouselQAStatus.PASS
    messages: list[str] = []
    for region in regions:
        x1, y1, x2, y2 = region.box
        if x1 < CANVAS.safe_left or y1 < CANVAS.safe_top or x2 > CANVAS.safe_right or y2 > CANVAS.safe_bottom:
            status = _max_status(status, CarouselQAStatus.FAIL)
            messages.append(f"{region.name} outside safe margins")
        if region.min_font_size < MIN_READABLE_FONT_SIZE:
            status = _max_status(status, CarouselQAStatus.WARNING)
            messages.append(f"{region.name} uses tiny font")
        if not region.text.strip():
            status = _max_status(status, CarouselQAStatus.FAIL)
            messages.append(f"{region.name} is empty")
    for left_index, left in enumerate(regions):
        for right in regions[left_index + 1:]:
            if _overlap(left.box, right.box):
                status = _max_status(status, CarouselQAStatus.WARNING)
                messages.append(f"{left.name} overlaps {right.name}")
    return status, messages


def qa_image_files(paths: list[Path]) -> tuple[CarouselQAStatus, list[str]]:
    status = CarouselQAStatus.PASS
    messages: list[str] = []
    for path in paths:
        if not path.exists():
            status = _max_status(status, CarouselQAStatus.FAIL)
            messages.append(f"missing {path}")
            continue
        with Image.open(path) as image:
            if image.size != (CANVAS.width, CANVAS.height):
                status = _max_status(status, CarouselQAStatus.FAIL)
                messages.append(f"{path.name} has size {image.size}")
            if image.format != "PNG":
                status = _max_status(status, CarouselQAStatus.FAIL)
                messages.append(f"{path.name} is not PNG")
    return status, messages


def _copy_repeats(slide: CarouselSlide) -> bool:
    assert slide.item is not None
    headline = slide.item.headline.strip().lower()
    return headline in {
        slide.item.what_happened.strip().lower(),
        slide.item.why_it_matters.strip().lower(),
    }


def _overlap(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    return left[0] < right[2] and left[2] > right[0] and left[1] < right[3] and left[3] > right[1]


def _max_status(left: CarouselQAStatus, right: CarouselQAStatus) -> CarouselQAStatus:
    order = {
        CarouselQAStatus.PASS: 0,
        CarouselQAStatus.WARNING: 1,
        CarouselQAStatus.FAIL: 2,
    }
    return left if order[left] >= order[right] else right
