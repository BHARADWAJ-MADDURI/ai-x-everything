from pathlib import Path

from PIL import Image, ImageDraw

from src.editorial.formats import AIBriefPackage
from src.rendering.carousel.art_direction import BriefArtDirectionResolver, CarouselArtStyle
from src.rendering.carousel.director import AIBriefCarouselDirector
from src.rendering.carousel.layouts import SlideLayout, layout_for_slide, production_layout_for_slide
from src.rendering.carousel.models import (
    CANVAS,
    CarouselQAStatus,
    CarouselSlide,
    CarouselSlideType,
    CarouselVariant,
    CropStrategy,
    EditorialComposition,
    HumanVisualSelection,
    MediaAsset,
    RenderedCarousel,
    TextRegion,
    VisualRole,
)
from src.rendering.carousel.qa import qa_image_files, qa_slides
from src.rendering.carousel.typography import CarouselTypography
from src.rendering.fonts import FontResolver, TypographyRole


class AIBriefCarouselRenderer:
    """Render validated AI Brief packages as static PNG carousel slides."""

    def __init__(
        self,
        *,
        director: AIBriefCarouselDirector | None = None,
        art_resolver: BriefArtDirectionResolver | None = None,
        typography: CarouselTypography | None = None,
    ) -> None:
        self.director = director or AIBriefCarouselDirector()
        self.art_resolver = art_resolver or BriefArtDirectionResolver()
        self.typography = typography or CarouselTypography(FontResolver())

    def render(
        self,
        package: AIBriefPackage,
        *,
        variant: CarouselVariant,
        output_dir: Path,
        visual_selections: dict[str, HumanVisualSelection] | None = None,
        media_assets: dict[str, MediaAsset] | None = None,
        production: bool = False,
    ) -> RenderedCarousel:
        if not package.validation.ready:
            raise ValueError("AI Brief package must validate before rendering")
        output_dir.mkdir(parents=True, exist_ok=True)
        slides = self.director.build_slides(
            package,
            variant,
            visual_selections=visual_selections,
            media_assets=media_assets,
        )
        slide_paths: list[Path] = []
        rendered_slides: list[CarouselSlide] = []
        for slide in slides:
            if production:
                slide = _with_production_composition(slide)
            rendered_slide, image = self._render_slide(slide, package, production=production)
            rendered_slides.append(rendered_slide)
            path = output_dir / _slide_filename(rendered_slide)
            image.save(path)
            slide_paths.append(path)
        contact_sheet_path = output_dir / "contact_sheet.png"
        _build_contact_sheet(slide_paths, contact_sheet_path)
        status, messages = qa_slides(rendered_slides, package, check_repeated_copy=production)
        image_status, image_messages = qa_image_files(slide_paths)
        status = _max_status(status, image_status)
        messages.extend(image_messages)
        return RenderedCarousel(
            variant=variant,
            output_dir=output_dir,
            slide_paths=slide_paths,
            contact_sheet_path=contact_sheet_path,
            qa_status=status,
            qa_messages=messages,
        )

    def _render_slide(
        self,
        slide: CarouselSlide,
        package: AIBriefPackage,
        *,
        production: bool,
    ) -> tuple[CarouselSlide, Image.Image]:
        style = self.art_resolver.resolve_style(
            variant=slide.variant,
            category=slide.category,
            headline=slide.title,
        )
        layout = production_layout_for_slide(slide) if production else layout_for_slide(slide)
        image = Image.new("RGB", (CANVAS.width, CANVAS.height), style.palette.background)
        draw = ImageDraw.Draw(image)
        _draw_background(draw, style, layout)
        regions: list[TextRegion] = []
        if slide.slide_type is CarouselSlideType.COVER:
            regions = self._draw_cover(draw, slide, package, style, layout, production=production)
        elif slide.slide_type is CarouselSlideType.OUTRO:
            regions = self._draw_outro(draw, slide, style, layout)
        else:
            regions = self._draw_story(image, draw, slide, style, layout, production=production)
        return (
            CarouselSlide(
                position=slide.position,
                slide_type=slide.slide_type,
                variant=slide.variant,
                title=slide.title,
                subtitle=slide.subtitle,
                item=slide.item,
                category=slide.category,
                source_label=slide.source_label,
                visual_role=slide.visual_role,
                media_asset=slide.media_asset,
                media_attribution=slide.media_attribution,
                layout_composition=slide.layout_composition,
                diagram_spec=slide.diagram_spec,
                graphic_spec=slide.graphic_spec,
                teasers=slide.teasers,
                text_regions=regions,
            ),
            image,
        )

    def _draw_cover(
        self,
        draw: ImageDraw.ImageDraw,
        slide: CarouselSlide,
        package: AIBriefPackage,
        style: CarouselArtStyle,
        layout: SlideLayout,
        *,
        production: bool,
    ) -> list[TextRegion]:
        regions = []
        _draw_cover_motif(draw, style, layout)
        regions.append(_draw_text_box(self.typography, draw, layout.brand_box, "EVERYTHING × AI", TypographyRole.MONO, 28, 20, style.palette.muted))
        if production:
            regions.append(_draw_text_box(self.typography, draw, layout.label_box, "THE\nAI BRIEF", style.headline_role, 82, 46, style.palette.ink))
            regions.append(_draw_text_box(self.typography, draw, layout.headline_box, slide.subtitle or "", style.body_role, 38, 24, style.palette.ink))
            teaser_text = "\n".join(f"{index:02d}  {teaser}" for index, teaser in enumerate(slide.teasers, start=1))
            regions.append(_draw_text_box(self.typography, draw, layout.what_box, teaser_text, style.body_role, 34, 22, style.palette.ink))
            regions.append(_draw_text_box(self.typography, draw, layout.why_box, "Understand what's changing.", style.body_role, 34, 24, style.palette.ink))
            regions.append(_draw_text_box(self.typography, draw, layout.source_box, package.date.isoformat(), style.label_role, 24, 18, style.palette.muted))
            return regions
        regions.append(_draw_text_box(self.typography, draw, layout.label_box, slide.title, style.headline_role, 88, 48, style.palette.ink))
        regions.append(_draw_text_box(self.typography, draw, layout.headline_box, slide.subtitle or "", style.body_role, 50, 28, style.palette.ink))
        regions.append(_draw_text_box(self.typography, draw, layout.what_box, package.date.isoformat(), style.label_role, 28, 20, style.palette.muted))
        regions.append(_draw_text_box(self.typography, draw, layout.why_box, "Understand what's changing.", style.body_role, 36, 24, style.palette.ink))
        return regions

    def _draw_story(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        slide: CarouselSlide,
        style: CarouselArtStyle,
        layout: SlideLayout,
        *,
        production: bool,
    ) -> list[TextRegion]:
        assert slide.item is not None
        if production:
            _draw_production_visual(image, draw, slide, style, layout)
        else:
            _draw_motif(draw, style, layout)
        index_label = f"{slide.item.position:02d} / {slide.category.upper() if slide.category else 'AI'}"
        regions = [
            _draw_text_box(self.typography, draw, layout.brand_box, "EVERYTHING × AI", TypographyRole.MONO, 20, 18, style.palette.muted),
            _draw_text_box(self.typography, draw, layout.label_box, index_label, style.label_role, 24, 18, style.palette.accent),
            _draw_text_box(self.typography, draw, layout.headline_box, slide.title, style.headline_role, 58, 34, style.palette.ink),
            _draw_text_box(self.typography, draw, layout.what_box, "WHAT HAPPENED\n" + slide.item.what_happened, style.body_role, 30, 20, style.palette.ink),
            _draw_text_box(self.typography, draw, layout.why_box, "WHY IT MATTERS\n" + slide.item.why_it_matters, style.body_role, 30, 20, style.palette.ink),
            _draw_text_box(self.typography, draw, layout.source_box, slide.source_label or "", style.label_role, 21, 18, style.palette.muted),
        ]
        if slide.media_attribution:
            regions.append(_draw_text_box(self.typography, draw, _media_attribution_box(layout), "PHOTO · " + slide.media_attribution, style.label_role, 19, 18, style.palette.muted))
        return regions

    def _draw_outro(
        self,
        draw: ImageDraw.ImageDraw,
        slide: CarouselSlide,
        style: CarouselArtStyle,
        layout: SlideLayout,
    ) -> list[TextRegion]:
        _draw_motif(draw, style, layout)
        return [
            _draw_text_box(self.typography, draw, layout.brand_box, slide.title, style.headline_role, 64, 34, style.palette.ink),
            _draw_text_box(self.typography, draw, layout.label_box, slide.subtitle or "", style.body_role, 34, 22, style.palette.ink),
            _draw_text_box(self.typography, draw, layout.headline_box, "Which story should we\nbreak down next?", style.headline_role, 56, 32, style.palette.ink),
            _draw_text_box(self.typography, draw, layout.source_box, "Follow for the next AI Brief", style.label_role, 24, 18, style.palette.muted),
        ]


def _draw_background(draw: ImageDraw.ImageDraw, style: CarouselArtStyle, layout: SlideLayout) -> None:
    p = style.palette
    if style.variant is CarouselVariant.EDITORIAL:
        draw.rectangle((48, 48, CANVAS.width - 48, CANVAS.height - 48), fill=p.paper)
        draw.line((CANVAS.safe_left, 205, CANVAS.safe_right, 205), fill=p.rule, width=2)
        draw.rectangle((CANVAS.safe_left, CANVAS.safe_bottom + 18, CANVAS.safe_right, CANVAS.safe_bottom + 22), fill=p.accent)
    else:
        for x in range(0, CANVAS.width, 72):
            draw.line((x, 0, x, CANVAS.height), fill=p.grid, width=1)
        for y in range(0, CANVAS.height, 72):
            draw.line((0, y, CANVAS.width, y), fill=p.grid, width=1)
        draw.rounded_rectangle((54, 54, CANVAS.width - 54, CANVAS.height - 54), radius=26, outline=p.rule, width=2)
        draw.rectangle((CANVAS.safe_left, 210, CANVAS.safe_right, 216), fill=p.accent)
    draw.rectangle((layout.visual_box[0], layout.visual_box[1], layout.visual_box[2], layout.visual_box[3]), outline=p.rule, width=2)


def _draw_production_visual(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    slide: CarouselSlide,
    style: CarouselArtStyle,
    layout: SlideLayout,
) -> None:
    p = style.palette
    x1, y1, x2, y2 = layout.visual_box
    if slide.visual_role in {VisualRole.SOURCE_MEDIA, VisualRole.LICENSED_MEDIA} and slide.media_asset and slide.media_asset.local_path:
        _draw_media_asset(image, slide.media_asset, layout.visual_box)
        draw.rectangle((x1, y1, x2, y2), outline=p.rule, width=2)
        draw.line((x1 + 24, y2 - 44, x2 - 24, y2 - 44), fill=p.paper, width=2)
        return
    if slide.visual_role is VisualRole.EXPLAINER_DIAGRAM:
        _draw_diagram(draw, style, layout)
        return
    if slide.visual_role is VisualRole.EDITORIAL_GRAPHIC:
        _draw_editorial_graphic(draw, style, layout)
        return
    if slide.layout_composition is EditorialComposition.DOCUMENT_POLICY:
        _draw_document_graphic(draw, style, layout)
        return
    _draw_typography_fallback_visual(draw, style, layout)


def _draw_media_asset(slide_image: Image.Image, asset: MediaAsset, box: tuple[int, int, int, int]) -> None:
    assert asset.local_path is not None
    x1, y1, x2, y2 = box
    with Image.open(asset.local_path) as source_image:
        source_image = source_image.convert("RGB")
        from src.rendering.carousel.media import normalize_image

        rendered = normalize_image(
            source_image,
            target_size=(x2 - x1, y2 - y1),
            crop_strategy=asset.crop_strategy,
            focal_point=asset.focal_point,
        )
        slide_image.paste(rendered, (x1, y1))


def _draw_diagram(draw: ImageDraw.ImageDraw, style: CarouselArtStyle, layout: SlideLayout) -> None:
    p = style.palette
    x1, y1, x2, y2 = layout.visual_box
    node_w = (x2 - x1 - 90) // 3
    cy = y1 + (y2 - y1) // 2
    nodes = []
    for index, label in enumerate(("Verified input", "System change", "Practical effect")):
        nx1 = x1 + 24 + index * (node_w + 32)
        nx2 = nx1 + node_w
        draw.rounded_rectangle((nx1, cy - 52, nx2, cy + 52), radius=10, outline=p.accent, fill=p.paper, width=3)
        draw.line((nx2, cy, nx2 + 30, cy), fill=p.rule, width=3)
        nodes.append((label, nx1, cy - 30, nx2, cy + 30))
    for label, nx1, ny1, nx2, ny2 in nodes:
        draw.text((nx1 + 16, ny1 + 8), label, fill=p.ink)


def _draw_editorial_graphic(draw: ImageDraw.ImageDraw, style: CarouselArtStyle, layout: SlideLayout) -> None:
    p = style.palette
    x1, y1, x2, y2 = layout.visual_box
    draw.rectangle((x1 + 26, y1 + 26, x2 - 26, y2 - 26), outline=p.rule, width=2)
    for index, height in enumerate((80, 170, 250)):
        bx1 = x1 + 65 + index * 96
        draw.rectangle((bx1, y2 - 72 - height, bx1 + 54, y2 - 72), fill=p.accent if index == 2 else p.rule)
    draw.line((x1 + 48, y2 - 72, x2 - 48, y2 - 72), fill=p.ink, width=2)
    draw.ellipse((x2 - 120, y1 + 60, x2 - 60, y1 + 120), outline=p.accent_alt, width=5)


def _draw_document_graphic(draw: ImageDraw.ImageDraw, style: CarouselArtStyle, layout: SlideLayout) -> None:
    p = style.palette
    x1, y1, x2, y2 = layout.visual_box
    draw.rectangle((x1 + 45, y1 + 35, x2 - 45, y2 - 35), fill=p.paper, outline=p.rule, width=2)
    for offset in (95, 150, 205, 300):
        draw.line((x1 + 90, y1 + offset, x2 - 90, y1 + offset), fill=p.rule, width=3)
    draw.rectangle((x1 + 90, y1 + 245, x2 - 165, y1 + 255), fill=p.accent)


def _draw_typography_fallback_visual(draw: ImageDraw.ImageDraw, style: CarouselArtStyle, layout: SlideLayout) -> None:
    p = style.palette
    x1, y1, x2, y2 = layout.visual_box
    draw.rectangle((x1, y1 + 18, x2, y1 + 25), fill=p.accent)
    draw.rectangle((x1, y1 + 55, x1 + 300, y1 + 61), fill=p.rule)
    draw.rectangle((x2 - 240, y1 + 55, x2, y1 + 61), fill=p.accent_alt)


def _media_attribution_box(layout: SlideLayout) -> tuple[int, int, int, int]:
    x1, y1, x2, _ = layout.source_box
    return (x1, y1 + 35, x2, y1 + 70)


def _with_production_composition(slide: CarouselSlide) -> CarouselSlide:
    if slide.slide_type is not CarouselSlideType.STORY:
        return slide
    composition = EditorialComposition.TEXT_EDITORIAL
    if slide.visual_role in {VisualRole.SOURCE_MEDIA, VisualRole.LICENSED_MEDIA}:
        composition = EditorialComposition.PHOTO_DOMINANT
    elif slide.visual_role is VisualRole.EXPLAINER_DIAGRAM:
        composition = EditorialComposition.DIAGRAM_EXPLAINER
    elif slide.visual_role is VisualRole.EDITORIAL_GRAPHIC:
        composition = EditorialComposition.DATA_EDITORIAL
    elif slide.category and any(token in slide.category.lower() for token in ("policy", "workforce", "regulation")):
        composition = EditorialComposition.DOCUMENT_POLICY
    return CarouselSlide(
        position=slide.position,
        slide_type=slide.slide_type,
        variant=slide.variant,
        title=slide.title,
        subtitle=slide.subtitle,
        item=slide.item,
        category=slide.category,
        source_label=slide.source_label,
        visual_role=slide.visual_role,
        media_asset=slide.media_asset,
        media_attribution=slide.media_attribution,
        layout_composition=composition,
        diagram_spec=slide.diagram_spec,
        graphic_spec=slide.graphic_spec,
        teasers=slide.teasers,
        text_regions=slide.text_regions,
    )


def _draw_motif(draw: ImageDraw.ImageDraw, style: CarouselArtStyle, layout: SlideLayout) -> None:
    x1, y1, x2, y2 = layout.visual_box
    p = style.palette
    if style.variant is CarouselVariant.EDITORIAL:
        draw.line((x1 + 24, y1 + 34, x2 - 24, y2 - 34), fill=p.accent, width=5)
        draw.line((x1 + 24, y2 - 34, x2 - 24, y1 + 34), fill=p.rule, width=2)
        draw.ellipse((x1 + 42, y1 + 42, x1 + 102, y1 + 102), outline=p.accent_alt, width=4)
        return
    for offset in range(30, max(31, x2 - x1), 58):
        draw.line((x1 + offset, y1 + 30, x1 + offset // 2, y2 - 36), fill=p.rule, width=2)
    draw.rounded_rectangle((x1 + 40, y1 + 50, x2 - 40, y1 + 110), radius=12, outline=p.accent, width=3)
    draw.ellipse((x2 - 120, y2 - 120, x2 - 52, y2 - 52), outline=p.accent_alt, width=4)


def _draw_cover_motif(draw: ImageDraw.ImageDraw, style: CarouselArtStyle, layout: SlideLayout) -> None:
    x1, y1, x2, y2 = layout.visual_box
    p = style.palette
    if style.variant is CarouselVariant.EDITORIAL:
        draw.rectangle((x1 + 22, y1 + 24, x2 - 22, y1 + 28), fill=p.accent)
        draw.rectangle((x1 + 22, y1 + 78, x2 - 82, y1 + 82), fill=p.rule)
        draw.line((x2 - 58, y1 + 24, x2 - 58, y2 - 22), fill=p.accent_alt, width=3)
        draw.ellipse((x2 - 96, y2 - 74, x2 - 50, y2 - 28), outline=p.accent, width=4)
        return
    for offset in range(0, x2 - x1, 42):
        draw.line((x1 + offset, y1 + 22, x1 + offset + 80, y2 - 24), fill=p.rule, width=1)
    draw.rounded_rectangle((x1 + 32, y1 + 48, x2 - 32, y1 + 108), radius=10, outline=p.accent, width=3)
    draw.line((x1 + 32, y2 - 46, x2 - 32, y2 - 46), fill=p.accent_alt, width=3)


def _draw_text_box(
    typography: CarouselTypography,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    role: TypographyRole,
    preferred_size: int,
    min_size: int,
    fill: tuple[int, int, int],
) -> TextRegion:
    x1, y1, x2, y2 = box
    fitted = typography.fit_text(
        text=text,
        role=role,
        max_width=x2 - x1,
        max_height=y2 - y1,
        preferred_size=preferred_size,
        min_size=min_size,
        line_spacing=max(8, preferred_size // 4),
    )
    actual = typography.draw_fitted(draw, (x1, y1), fitted, fill, line_spacing=max(8, fitted.font_size // 4))
    if fitted.overflow:
        actual = (actual[0], actual[1], max(actual[2], x2 + 1), max(actual[3], y2 + 1))
    return TextRegion(name=text.split("\n", 1)[0][:32] or "text", box=actual, min_font_size=fitted.font_size, text=text)


def _build_contact_sheet(slide_paths: list[Path], output_path: Path) -> None:
    thumbs: list[Image.Image] = []
    thumb_width = 270
    thumb_height = 338
    for path in slide_paths:
        with Image.open(path) as image:
            thumb = image.copy()
            thumb.thumbnail((thumb_width, thumb_height))
            canvas = Image.new("RGB", (thumb_width, thumb_height), (245, 245, 245))
            canvas.paste(thumb, ((thumb_width - thumb.width) // 2, (thumb_height - thumb.height) // 2))
            thumbs.append(canvas)
    cols = min(4, max(1, len(thumbs)))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_width, rows * thumb_height), (225, 225, 225))
    for index, thumb in enumerate(thumbs):
        x = (index % cols) * thumb_width
        y = (index // cols) * thumb_height
        sheet.paste(thumb, (x, y))
    sheet.save(output_path)


def _slide_filename(slide: CarouselSlide) -> str:
    if slide.slide_type is CarouselSlideType.COVER:
        suffix = "cover"
    elif slide.slide_type is CarouselSlideType.OUTRO:
        suffix = "outro"
    else:
        suffix = "story"
    return f"slide_{slide.position:02d}_{suffix}.png"


def _max_status(left: CarouselQAStatus, right: CarouselQAStatus) -> CarouselQAStatus:
    order = {CarouselQAStatus.PASS: 0, CarouselQAStatus.WARNING: 1, CarouselQAStatus.FAIL: 2}
    return left if order[left] >= order[right] else right
