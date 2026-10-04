from dataclasses import dataclass

from src.rendering.carousel.models import CANVAS, CarouselSlide, CarouselSlideType, CarouselVariant, EditorialComposition


@dataclass(frozen=True)
class SlideLayout:
    brand_box: tuple[int, int, int, int]
    label_box: tuple[int, int, int, int]
    headline_box: tuple[int, int, int, int]
    what_box: tuple[int, int, int, int]
    why_box: tuple[int, int, int, int]
    source_box: tuple[int, int, int, int]
    visual_box: tuple[int, int, int, int]


def layout_for_slide(slide: CarouselSlide) -> SlideLayout:
    if slide.variant is CarouselVariant.DYNAMIC:
        return _dynamic_layout(slide.slide_type)
    return _editorial_layout(slide.slide_type)


def _editorial_layout(slide_type: CarouselSlideType) -> SlideLayout:
    if slide_type is CarouselSlideType.COVER:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 112, 520, 170),
            label_box=(CANVAS.safe_left, 270, CANVAS.safe_right, 350),
            headline_box=(CANVAS.safe_left, 375, CANVAS.safe_right, 660),
            what_box=(CANVAS.safe_left, 720, CANVAS.safe_right, 820),
            why_box=(CANVAS.safe_left, 860, CANVAS.safe_right, 980),
            source_box=(CANVAS.safe_left, 1155, CANVAS.safe_right, 1210),
            visual_box=(610, 120, CANVAS.safe_right, 300),
        )
    if slide_type is CarouselSlideType.OUTRO:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 170, CANVAS.safe_right, 250),
            label_box=(CANVAS.safe_left, 315, CANVAS.safe_right, 390),
            headline_box=(CANVAS.safe_left, 510, CANVAS.safe_right, 760),
            what_box=(CANVAS.safe_left, 825, CANVAS.safe_right, 910),
            why_box=(CANVAS.safe_left, 980, CANVAS.safe_right, 1060),
            source_box=(CANVAS.safe_left, 1130, CANVAS.safe_right, 1190),
            visual_box=(CANVAS.safe_left, 350, CANVAS.safe_right, 470),
        )
    return SlideLayout(
        brand_box=(CANVAS.safe_left, CANVAS.safe_top, 480, 140),
        label_box=(CANVAS.safe_left, 150, CANVAS.safe_right, 200),
        headline_box=(CANVAS.safe_left, 245, CANVAS.safe_right - 110, 500),
        what_box=(CANVAS.safe_left, 610, CANVAS.safe_right - 70, 750),
        why_box=(CANVAS.safe_left + 74, 840, CANVAS.safe_right, 1005),
        source_box=(CANVAS.safe_left, 1165, CANVAS.safe_right, 1215),
        visual_box=(700, 505, CANVAS.safe_right, 805),
    )


def production_layout_for_slide(slide: CarouselSlide) -> SlideLayout:
    if slide.slide_type is CarouselSlideType.COVER:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 92, 520, 140),
            label_box=(CANVAS.safe_left, 205, CANVAS.safe_right, 390),
            headline_box=(CANVAS.safe_left, 420, CANVAS.safe_right, 500),
            what_box=(CANVAS.safe_left, 570, CANVAS.safe_right, 970),
            why_box=(CANVAS.safe_left, 1070, CANVAS.safe_right, 1140),
            source_box=(CANVAS.safe_left, 1180, CANVAS.safe_right, 1235),
            visual_box=(650, 92, CANVAS.safe_right, 170),
        )
    if slide.slide_type is CarouselSlideType.OUTRO:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 150, CANVAS.safe_right, 230),
            label_box=(CANVAS.safe_left, 300, CANVAS.safe_right, 370),
            headline_box=(CANVAS.safe_left, 500, CANVAS.safe_right, 760),
            what_box=(CANVAS.safe_left, 830, CANVAS.safe_right, 920),
            why_box=(CANVAS.safe_left, 990, CANVAS.safe_right, 1070),
            source_box=(CANVAS.safe_left, 1145, CANVAS.safe_right, 1205),
            visual_box=(CANVAS.safe_left, 405, CANVAS.safe_right, 465),
        )
    if slide.layout_composition is EditorialComposition.PHOTO_DOMINANT:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 92, 520, 138),
            label_box=(CANVAS.safe_left, 155, CANVAS.safe_right, 200),
            headline_box=(CANVAS.safe_left, 225, CANVAS.safe_right, 390),
            what_box=(CANVAS.safe_left, 905, 520, 1085),
            why_box=(570, 905, CANVAS.safe_right, 1085),
            source_box=(CANVAS.safe_left, 1160, CANVAS.safe_right, 1230),
            visual_box=(CANVAS.safe_left, 430, CANVAS.safe_right, 850),
        )
    if slide.layout_composition is EditorialComposition.DIAGRAM_EXPLAINER:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 92, 520, 138),
            label_box=(CANVAS.safe_left, 155, CANVAS.safe_right, 200),
            headline_box=(CANVAS.safe_left, 230, CANVAS.safe_right, 405),
            what_box=(CANVAS.safe_left, 840, 515, 1020),
            why_box=(560, 840, CANVAS.safe_right, 1020),
            source_box=(CANVAS.safe_left, 1160, CANVAS.safe_right, 1230),
            visual_box=(CANVAS.safe_left, 455, CANVAS.safe_right, 785),
        )
    if slide.layout_composition is EditorialComposition.DATA_EDITORIAL:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 92, 520, 138),
            label_box=(CANVAS.safe_left, 155, CANVAS.safe_right, 200),
            headline_box=(CANVAS.safe_left, 225, 620, 475),
            what_box=(CANVAS.safe_left, 640, 525, 820),
            why_box=(CANVAS.safe_left, 900, CANVAS.safe_right, 1075),
            source_box=(CANVAS.safe_left, 1160, CANVAS.safe_right, 1230),
            visual_box=(665, 245, CANVAS.safe_right, 760),
        )
    if slide.layout_composition is EditorialComposition.DOCUMENT_POLICY:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 92, 520, 138),
            label_box=(CANVAS.safe_left, 155, CANVAS.safe_right, 200),
            headline_box=(CANVAS.safe_left, 230, CANVAS.safe_right, 430),
            what_box=(CANVAS.safe_left, 500, 525, 700),
            why_box=(CANVAS.safe_left, 760, 525, 970),
            source_box=(CANVAS.safe_left, 1160, CANVAS.safe_right, 1230),
            visual_box=(610, 500, CANVAS.safe_right, 970),
        )
    return SlideLayout(
        brand_box=(CANVAS.safe_left, 92, 520, 138),
        label_box=(CANVAS.safe_left, 155, CANVAS.safe_right, 200),
        headline_box=(CANVAS.safe_left, 250, CANVAS.safe_right, 520),
        what_box=(CANVAS.safe_left, 610, CANVAS.safe_right, 775),
        why_box=(CANVAS.safe_left, 860, CANVAS.safe_right, 1045),
        source_box=(CANVAS.safe_left, 1160, CANVAS.safe_right, 1230),
        visual_box=(CANVAS.safe_left, 1075, CANVAS.safe_right, 1125),
    )


def _dynamic_layout(slide_type: CarouselSlideType) -> SlideLayout:
    if slide_type is CarouselSlideType.COVER:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 90, 560, 150),
            label_box=(CANVAS.safe_left, 220, CANVAS.safe_right, 285),
            headline_box=(CANVAS.safe_left, 330, CANVAS.safe_right, 610),
            what_box=(CANVAS.safe_left, 700, CANVAS.safe_right, 805),
            why_box=(CANVAS.safe_left, 875, CANVAS.safe_right, 975),
            source_box=(CANVAS.safe_left, 1160, CANVAS.safe_right, 1210),
            visual_box=(CANVAS.safe_left, 650, CANVAS.safe_right, 1120),
        )
    if slide_type is CarouselSlideType.OUTRO:
        return SlideLayout(
            brand_box=(CANVAS.safe_left, 150, CANVAS.safe_right, 230),
            label_box=(CANVAS.safe_left, 300, CANVAS.safe_right, 365),
            headline_box=(CANVAS.safe_left, 485, CANVAS.safe_right, 735),
            what_box=(CANVAS.safe_left, 820, CANVAS.safe_right, 900),
            why_box=(CANVAS.safe_left, 970, CANVAS.safe_right, 1055),
            source_box=(CANVAS.safe_left, 1135, CANVAS.safe_right, 1190),
            visual_box=(CANVAS.safe_left, 380, CANVAS.safe_right, 460),
        )
    return SlideLayout(
        brand_box=(CANVAS.safe_left, CANVAS.safe_top, 520, 140),
        label_box=(CANVAS.safe_left, 162, CANVAS.safe_right, 215),
        headline_box=(CANVAS.safe_left, 250, CANVAS.safe_right, 450),
        what_box=(CANVAS.safe_left, 535, 650, 725),
        why_box=(CANVAS.safe_left, 810, 740, 1015),
        source_box=(CANVAS.safe_left, 1160, CANVAS.safe_right, 1215),
        visual_box=(705, 505, CANVAS.safe_right, 1035),
    )
