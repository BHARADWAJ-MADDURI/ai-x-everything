from pathlib import Path

from PIL import Image

from src.editorial.formats import AIBriefPackage
from src.rendering.carousel.models import CANVAS, CarouselQAStatus, CarouselSlide, CarouselSlideType, TextRegion


MIN_READABLE_FONT_SIZE = 18


def qa_slides(slides: list[CarouselSlide], package: AIBriefPackage) -> tuple[CarouselQAStatus, list[str]]:
    messages: list[str] = []
    status = CarouselQAStatus.PASS
    expected_count = package.item_count + 2
    if len(slides) != expected_count:
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append(f"slide count {len(slides)} did not match expected {expected_count}")
    positions = [slide.position for slide in slides]
    if len(set(positions)) != len(positions):
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("duplicate slide position")
    cover = slides[0] if slides else None
    if cover is None or cover.slide_type is not CarouselSlideType.COVER or "AI BRIEF" not in cover.title:
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("cover missing AI Brief brand")
    if cover and (cover.subtitle or "") != package.subtitle:
        status = _max_status(status, CarouselQAStatus.FAIL)
        messages.append("cover count does not match actual Brief item count")

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
        region_status, region_messages = qa_text_regions(slide.text_regions)
        status = _max_status(status, region_status)
        messages.extend(f"slide {slide.position}: {message}" for message in region_messages)
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


def _overlap(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    return left[0] < right[2] and left[2] > right[0] and left[1] < right[3] and left[3] > right[1]


def _max_status(left: CarouselQAStatus, right: CarouselQAStatus) -> CarouselQAStatus:
    order = {
        CarouselQAStatus.PASS: 0,
        CarouselQAStatus.WARNING: 1,
        CarouselQAStatus.FAIL: 2,
    }
    return left if order[left] >= order[right] else right
