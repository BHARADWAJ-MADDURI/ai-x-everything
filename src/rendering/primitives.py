from PIL import Image, ImageDraw, ImageFont

from src.rendering.style import SafeZone, VisualStyle


Frame = Image.Image


def text_bbox(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
) -> tuple[int, int, int, int]:
    return draw.textbbox((0, 0), text, font=font)


def wrap_text(
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    draw: ImageDraw.ImageDraw | None = None,
) -> list[str]:
    """Wrap text so every line fits within max_width."""

    local_image = None
    if draw is None:
        local_image = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(local_image)

    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if text_bbox(draw, candidate, font)[2] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
        if current:
            lines.append(current)
    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    max_width: int,
    line_spacing: int = 12,
) -> tuple[int, int, int, int]:
    """Draw wrapped text and return its bounding box."""

    x, y = xy
    max_right = x
    current_y = y
    for line in wrap_text(text, font, max_width, draw):
        bbox = text_bbox(draw, line, font)
        draw.text((x, current_y), line, font=font, fill=fill)
        max_right = max(max_right, x + bbox[2])
        current_y += bbox[3] - bbox[1] + line_spacing
    return (x, y, max_right, current_y - line_spacing)


def draw_editorial_rule(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    style: VisualStyle,
    thickness: int = 5,
) -> None:
    draw.rounded_rectangle((x, y, x + width, y + thickness), radius=thickness, fill=style.accent)


def draw_label_pill(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    style: VisualStyle,
) -> tuple[int, int, int, int]:
    bbox = text_bbox(draw, text, font)
    x, y = xy
    padding_x = 24
    padding_y = 12
    rect = (x, y, x + bbox[2] + padding_x * 2, y + bbox[3] + padding_y * 2)
    draw.rounded_rectangle(rect, radius=22, fill=style.surface, outline=style.accent, width=2)
    draw.text((x + padding_x, y + padding_y - 2), text, font=font, fill=style.text)
    return rect


def draw_marker_highlight(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    style: VisualStyle,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 - 8, y2 - 24, x2 + 8, y2 + 8), radius=10, fill=style.marker)


def draw_emphasis_underline(
    draw: ImageDraw.ImageDraw,
    text_box: tuple[int, int, int, int],
    style: VisualStyle,
    offset: int = 14,
    thickness: int = 8,
) -> tuple[int, int, int, int]:
    """Draw an intentional underline below an emphasized phrase."""

    x1, _y1, x2, y2 = text_box
    line_box = (x1, y2 + offset, x2, y2 + offset + thickness)
    draw.rounded_rectangle(line_box, radius=thickness, fill=style.marker)
    return line_box


def draw_subtitle(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    style: VisualStyle,
    safe_zone: SafeZone,
) -> tuple[int, int, int, int]:
    bbox = text_bbox(draw, text, font)
    padding_x = 24
    padding_y = 10
    width = bbox[2] + padding_x * 2
    x = safe_zone.left + (safe_zone.width - width) // 2
    y = safe_zone.bottom - 105
    rect = (x, y, x + width, y + bbox[3] + padding_y * 2)
    draw.rounded_rectangle(rect, radius=12, fill=style.surface, outline=style.accent, width=2)
    draw.rounded_rectangle((x, y, x + 8, rect[3]), radius=4, fill=style.accent)
    draw.text((x + padding_x, y + padding_y - 2), text, font=font, fill=style.text)
    return rect


def draw_subtle_grid(draw: ImageDraw.ImageDraw, style: VisualStyle, spacing: int = 90) -> None:
    for x in range(0, 1080, spacing):
        draw.line((x, 0, x, 1920), fill=style.grid, width=1)
    for y in range(0, 1920, spacing):
        draw.line((0, y, 1080, y), fill=style.grid, width=1)


def assert_box_inside_safe_zone(
    box: tuple[int, int, int, int],
    safe_zone: SafeZone,
) -> bool:
    x1, y1, x2, y2 = box
    return x1 >= safe_zone.left and y1 >= safe_zone.top and x2 <= safe_zone.right and y2 <= safe_zone.bottom
