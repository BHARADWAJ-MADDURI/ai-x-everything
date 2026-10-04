from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from src.rendering.fonts import FontResolver, TypographyRole
from src.rendering.primitives import text_bbox, wrap_text


@dataclass(frozen=True)
class FittedText:
    text: str
    lines: list[str]
    font: ImageFont.ImageFont
    font_size: int
    box: tuple[int, int, int, int]
    overflow: bool


class CarouselTypography:
    def __init__(self, font_resolver: FontResolver | None = None) -> None:
        self.font_resolver = font_resolver or FontResolver()

    def fit_text(
        self,
        *,
        text: str,
        role: TypographyRole,
        max_width: int,
        max_height: int,
        preferred_size: int,
        min_size: int,
        line_spacing: int,
    ) -> FittedText:
        image = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(image)
        for size in range(preferred_size, min_size - 1, -2):
            font = self.font_resolver.font(role, size)
            lines = wrap_text(text, font, max_width, draw)
            height = _lines_height(draw, lines, font, line_spacing)
            width = _lines_width(draw, lines, font)
            if height <= max_height and width <= max_width:
                return FittedText(
                    text=text,
                    lines=lines,
                    font=font,
                    font_size=size,
                    box=(0, 0, width, height),
                    overflow=False,
                )
        font = self.font_resolver.font(role, min_size)
        lines = wrap_text(text, font, max_width, draw)
        return FittedText(
            text=text,
            lines=lines,
            font=font,
            font_size=min_size,
            box=(0, 0, _lines_width(draw, lines, font), _lines_height(draw, lines, font, line_spacing)),
            overflow=True,
        )

    def draw_fitted(
        self,
        draw: ImageDraw.ImageDraw,
        xy: tuple[int, int],
        fitted: FittedText,
        fill: tuple[int, int, int],
        line_spacing: int,
    ) -> tuple[int, int, int, int]:
        x, y = xy
        current_y = y
        right = x
        for line in fitted.lines:
            bbox = text_bbox(draw, line, fitted.font)
            draw.text((x, current_y), line, font=fitted.font, fill=fill)
            right = max(right, x + bbox[2])
            current_y += bbox[3] - bbox[1] + line_spacing
        return (x, y, right, current_y - line_spacing)


def _lines_height(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    line_spacing: int,
) -> int:
    if not lines:
        return 0
    return sum(text_bbox(draw, line, font)[3] - text_bbox(draw, line, font)[1] for line in lines) + line_spacing * (len(lines) - 1)


def _lines_width(draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.ImageFont) -> int:
    if not lines:
        return 0
    return max(text_bbox(draw, line, font)[2] for line in lines)
