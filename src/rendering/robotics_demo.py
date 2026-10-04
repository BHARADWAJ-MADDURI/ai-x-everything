from dataclasses import dataclass
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw

from src.rendering.fonts import FontResolver
from src.rendering.primitives import (
    assert_box_inside_safe_zone,
    draw_emphasis_underline,
    draw_editorial_rule,
    draw_label_pill,
    draw_subtitle,
    draw_subtle_grid,
    draw_wrapped_text,
    text_bbox,
)
from src.rendering.style import ContentStyle, EditorialTone, StyleResolver, VisualStyle


WIDTH = 1080
HEIGHT = 1920
FPS = 30
SCENE_SECONDS = 3
VIDEO_SECONDS = 12


@dataclass(frozen=True)
class DemoContent:
    """Deterministic content for the Step 4B visual proof."""

    domain: str = "robotics"
    series_label: str = "ROBOTICS × AI"
    headline: str = "Robots are learning to understand natural-language instructions."
    technology_terms: tuple[str, str, str] = ("VISION", "LANGUAGE", "ACTION")
    result_label: str = "ROBOT ACTION"
    impact: str = "This could change how robots work alongside people."
    outro: str = "EVERYTHING × AI"
    outro_line: str = "Understand what's changing."


@dataclass(frozen=True)
class ScenePresentation:
    """Explicit scene-level art direction within a global video style."""

    scene_number: int
    subtitle: str
    preview_name: str
    style_override: ContentStyle | None = None


DEFAULT_SCENES: tuple[ScenePresentation, ...] = (
    ScenePresentation(1, "Robots are learning", "scene_1.png"),
    ScenePresentation(2, "Vision plus language", "scene_2.png"),
    ScenePresentation(3, "Alongside people", "scene_3.png"),
    ScenePresentation(4, "Understand what's changing", "scene_4.png"),
)

HYBRID_SCENES: tuple[ScenePresentation, ...] = (
    ScenePresentation(1, "Robots are learning", "scene_01_hook.png", ContentStyle.EDITORIAL_HUMAN),
    ScenePresentation(2, "Vision plus language", "scene_02_technology.png", ContentStyle.DYNAMIC_TECH),
    ScenePresentation(3, "Alongside people", "scene_03_human_impact.png", ContentStyle.EDITORIAL_HUMAN),
    ScenePresentation(4, "Understand what's changing", "scene_04_outro.png", ContentStyle.EDITORIAL_HUMAN),
)


class RoboticsDemoRenderer:
    """Pillow scene renderer for deterministic Step 4B demo assets."""

    def __init__(self, font_resolver: FontResolver | None = None) -> None:
        self.fonts = font_resolver or FontResolver()
        self.styles = StyleResolver()

    def render_scene(
        self,
        scene_number: int,
        *,
        style: VisualStyle,
        content: DemoContent,
        subtitle: str,
    ) -> Image.Image:
        frame = Image.new("RGB", (WIDTH, HEIGHT), style.background)
        draw = ImageDraw.Draw(frame)
        if scene_number == 1:
            self._scene_hook(draw, style, content)
        elif scene_number == 2:
            self._scene_technology(draw, style, content)
        elif scene_number == 3:
            self._scene_impact(draw, style, content)
        elif scene_number == 4:
            self._scene_outro(draw, style, content)
        else:
            raise ValueError(f"Unknown scene: {scene_number}")

        subtitle_font = self.fonts.font(style.body_role, 36)
        draw_subtitle(draw, subtitle, subtitle_font, style, style.safe_zone)
        return frame

    def resolve_scene_style(
        self,
        *,
        domain: str,
        global_style: ContentStyle,
        presentation: ScenePresentation,
    ) -> VisualStyle:
        """Resolve a scene style, inheriting the global style unless overridden."""

        return self.styles.resolve(
            domain=domain,
            content_style=presentation.style_override or global_style,
            editorial_tone=EditorialTone.NEUTRAL,
        )

    def render_stills(
        self,
        *,
        content_style: ContentStyle,
        preview_dir: Path,
        content: DemoContent | None = None,
        scenes: tuple[ScenePresentation, ...] = DEFAULT_SCENES,
    ) -> list[Path]:
        demo = content or DemoContent()
        preview_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for presentation in scenes:
            style = self.resolve_scene_style(
                domain=demo.domain,
                global_style=content_style,
                presentation=presentation,
            )
            frame = self.render_scene(
                presentation.scene_number,
                style=style,
                content=demo,
                subtitle=presentation.subtitle,
            )
            path = preview_dir / presentation.preview_name
            frame.save(path)
            paths.append(path)
        return paths

    def render_video(
        self,
        *,
        content_style: ContentStyle,
        preview_dir: Path,
        output_path: Path,
        content: DemoContent | None = None,
        scenes: tuple[ScenePresentation, ...] = DEFAULT_SCENES,
    ) -> Path:
        frames = self.render_stills(
            content_style=content_style,
            preview_dir=preview_dir,
            content=content,
            scenes=scenes,
        )
        list_path = preview_dir / "frames.txt"
        list_path.write_text(
            "".join(f"file '{path.resolve()}'\nduration {SCENE_SECONDS}\n" for path in frames)
            + f"file '{frames[-1].resolve()}'\n",
            encoding="utf-8",
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:sample_rate=48000:duration={VIDEO_SECONDS}",
            "-vf",
            f"fps={FPS},format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(command, check=True)
        return output_path

    def _scene_hook(self, draw: ImageDraw.ImageDraw, style: VisualStyle, content: DemoContent) -> None:
        if style.headline_role.name != "EDITORIAL_SERIF":
            draw_subtle_grid(draw, style, spacing=150)
        label_font = self.fonts.font(style.mono_role, 34)
        headline_font = self.fonts.font(style.headline_role, 88)
        body_font = self.fonts.font(style.body_role, 34)
        draw_label_pill(draw, (style.safe_zone.left, 190), content.series_label, label_font, style)
        draw_editorial_rule(draw, style.safe_zone.left, 315, 280, style)
        start_x = style.safe_zone.left
        y = 430
        line_spacing = 16
        lines = ["Robots are learning", "to understand", "natural-language", "instructions."]
        natural_language_box = (0, 0, 0, 0)
        for line in lines:
            bbox = text_bbox(draw, line, headline_font)
            draw.text((start_x, y), line, font=headline_font, fill=style.text)
            if line == "natural-language":
                natural_language_box = (start_x, y, start_x + bbox[2], y + bbox[3])
            y += bbox[3] - bbox[1] + line_spacing
        draw_emphasis_underline(draw, natural_language_box, style, offset=18, thickness=9)
        draw_wrapped_text(
            draw,
            (style.safe_zone.left, 1195),
            "TEST / DEVELOPMENT DESIGN PROOF",
            body_font,
            style.muted,
            style.safe_zone.width,
            line_spacing=8,
        )

    def _scene_technology(self, draw: ImageDraw.ImageDraw, style: VisualStyle, content: DemoContent) -> None:
        label_font = self.fonts.font(style.mono_role, 34)
        node_font = self.fonts.font(style.mono_role, 48)
        result_font = self.fonts.font(style.headline_role, 72)
        draw_label_pill(draw, (style.safe_zone.left, 180), "TECHNOLOGY", label_font, style)
        node_boxes = [(115, 440, 470, 620), (610, 440, 965, 620), (360, 790, 720, 970)]
        for index, box in enumerate(node_boxes):
            draw.rounded_rectangle(box, radius=30, fill=style.surface, outline=style.accent, width=4)
            term = content.technology_terms[index]
            bbox = text_bbox(draw, term, node_font)
            draw.text(
                (box[0] + (box[2] - box[0] - bbox[2]) // 2, box[1] + 60),
                term,
                font=node_font,
                fill=style.text,
            )
        draw.line((470, 530, 610, 530), fill=style.accent_alt, width=7)
        draw.line((540, 620, 540, 790), fill=style.accent_alt, width=7)
        draw.polygon([(540, 1025), (504, 970), (576, 970)], fill=style.accent_alt)
        result_box = (170, 1085, 910, 1295)
        draw.rounded_rectangle(result_box, radius=40, fill=style.surface_alt, outline=style.accent_alt, width=5)
        bbox = text_bbox(draw, content.result_label, result_font)
        draw.text((540 - bbox[2] // 2, 1160), content.result_label, font=result_font, fill=style.text)

    def _scene_impact(self, draw: ImageDraw.ImageDraw, style: VisualStyle, content: DemoContent) -> None:
        label_font = self.fonts.font(style.mono_role, 32)
        headline_font = self.fonts.font(style.headline_role, 78)
        body_font = self.fonts.font(style.body_role, 34)
        draw_label_pill(draw, (style.safe_zone.left, 190), "HUMAN IMPACT", label_font, style)
        draw.rounded_rectangle((110, 420, 970, 1185), radius=16, fill=style.surface)
        box = draw_wrapped_text(
            draw,
            (165, 535),
            "This could change\nhow robots work\nalongside people.",
            headline_font,
            style.text,
            800,
            line_spacing=16,
        )
        draw.line((165, box[3] + 34, 710, box[3] + 16), fill=style.accent_alt, width=10)
        draw_wrapped_text(
            draw,
            (style.safe_zone.left, 1265),
            "Careful framing: this is a demo concept, not a current-news claim.",
            body_font,
            style.muted,
            style.safe_zone.width,
            line_spacing=10,
        )

    def _scene_outro(self, draw: ImageDraw.ImageDraw, style: VisualStyle, content: DemoContent) -> None:
        headline_font = self.fonts.font(style.headline_role, 82)
        body_font = self.fonts.font(style.body_role, 42)
        draw_editorial_rule(draw, 360, 700, 360, style, thickness=7)
        bbox = text_bbox(draw, content.outro, headline_font)
        draw.text(((WIDTH - bbox[2]) // 2, 805), content.outro, font=headline_font, fill=style.text)
        sub_bbox = text_bbox(draw, content.outro_line, body_font)
        draw.text(((WIDTH - sub_bbox[2]) // 2, 930), content.outro_line, font=body_font, fill=style.muted)
        draw.rounded_rectangle((430, 1120, 650, 1132), radius=6, fill=style.accent)


def headline_within_safe_bounds(renderer: RoboticsDemoRenderer, style: VisualStyle, text: str) -> bool:
    frame = Image.new("RGB", (WIDTH, HEIGHT), style.background)
    draw = ImageDraw.Draw(frame)
    font = renderer.fonts.font(style.headline_role, 74)
    box = draw_wrapped_text(draw, (style.safe_zone.left, 440), text, font, style.text, style.safe_zone.width)
    return assert_box_inside_safe_zone(box, style.safe_zone)


def hook_emphasis_boxes(renderer: RoboticsDemoRenderer, style: VisualStyle) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Return text and underline boxes for the hook emphasis test."""

    frame = Image.new("RGB", (WIDTH, HEIGHT), style.background)
    draw = ImageDraw.Draw(frame)
    font = renderer.fonts.font(style.headline_role, 88)
    bbox = text_bbox(draw, "natural-language", font)
    text_box = (style.safe_zone.left, 430 + 2 * (bbox[3] - bbox[1] + 16), style.safe_zone.left + bbox[2], 430 + 2 * (bbox[3] - bbox[1] + 16) + bbox[3])
    underline_box = (text_box[0], text_box[3] + 18, text_box[2], text_box[3] + 27)
    return text_box, underline_box
