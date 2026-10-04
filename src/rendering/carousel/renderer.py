from pathlib import Path

from PIL import Image, ImageDraw

from src.editorial.formats import AIBriefPackage
from src.rendering.carousel.art_direction import BriefArtDirectionResolver, CarouselArtStyle
from src.rendering.carousel.director import AIBriefCarouselDirector
from src.rendering.carousel.layouts import SlideLayout, layout_for_slide
from src.rendering.carousel.models import (
    CANVAS,
    CarouselQAStatus,
    CarouselSlide,
    CarouselSlideType,
    CarouselVariant,
    RenderedCarousel,
    TextRegion,
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
    ) -> RenderedCarousel:
        if not package.validation.ready:
            raise ValueError("AI Brief package must validate before rendering")
        output_dir.mkdir(parents=True, exist_ok=True)
        slides = self.director.build_slides(package, variant)
        slide_paths: list[Path] = []
        rendered_slides: list[CarouselSlide] = []
        for slide in slides:
            rendered_slide, image = self._render_slide(slide, package)
            rendered_slides.append(rendered_slide)
            path = output_dir / _slide_filename(rendered_slide)
            image.save(path)
            slide_paths.append(path)
        contact_sheet_path = output_dir / "contact_sheet.png"
        _build_contact_sheet(slide_paths, contact_sheet_path)
        status, messages = qa_slides(rendered_slides, package)
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

    def _render_slide(self, slide: CarouselSlide, package: AIBriefPackage) -> tuple[CarouselSlide, Image.Image]:
        style = self.art_resolver.resolve_style(
            variant=slide.variant,
            category=slide.category,
            headline=slide.title,
        )
        layout = layout_for_slide(slide)
        image = Image.new("RGB", (CANVAS.width, CANVAS.height), style.palette.background)
        draw = ImageDraw.Draw(image)
        _draw_background(draw, style, layout)
        regions: list[TextRegion] = []
        if slide.slide_type is CarouselSlideType.COVER:
            regions = self._draw_cover(draw, slide, package, style, layout)
        elif slide.slide_type is CarouselSlideType.OUTRO:
            regions = self._draw_outro(draw, slide, style, layout)
        else:
            regions = self._draw_story(draw, slide, style, layout)
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
    ) -> list[TextRegion]:
        regions = []
        _draw_cover_motif(draw, style, layout)
        regions.append(_draw_text_box(self.typography, draw, layout.brand_box, "EVERYTHING × AI", TypographyRole.MONO, 28, 20, style.palette.muted))
        regions.append(_draw_text_box(self.typography, draw, layout.label_box, slide.title, style.headline_role, 88, 48, style.palette.ink))
        regions.append(_draw_text_box(self.typography, draw, layout.headline_box, slide.subtitle or "", style.body_role, 50, 28, style.palette.ink))
        regions.append(_draw_text_box(self.typography, draw, layout.what_box, package.date.isoformat(), style.label_role, 28, 20, style.palette.muted))
        regions.append(_draw_text_box(self.typography, draw, layout.why_box, "Understand what's changing.", style.body_role, 36, 24, style.palette.ink))
        return regions

    def _draw_story(
        self,
        draw: ImageDraw.ImageDraw,
        slide: CarouselSlide,
        style: CarouselArtStyle,
        layout: SlideLayout,
    ) -> list[TextRegion]:
        assert slide.item is not None
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
