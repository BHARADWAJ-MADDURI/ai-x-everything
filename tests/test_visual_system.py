from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from src.rendering.fonts import FontResolver, TypographyRole
from src.rendering.primitives import assert_box_inside_safe_zone, draw_subtitle, wrap_text
from src.rendering.robotics_demo import (
    DemoContent,
    HYBRID_SCENES,
    RoboticsDemoRenderer,
    ScenePresentation,
    headline_within_safe_bounds,
    hook_emphasis_boxes,
)
from src.rendering.style import ContentStyle, EditorialTone, StyleResolver


class VisualSystemTests(unittest.TestCase):
    def test_font_resolver_returns_usable_font(self) -> None:
        resolver = FontResolver()
        font = resolver.font(TypographyRole.SANS, 32)

        self.assertTrue(hasattr(font, "getbbox"))

    def test_missing_preferred_font_falls_back_safely(self) -> None:
        resolver = FontResolver({TypographyRole.SANS: ["/missing/font.ttf"]})
        font = resolver.font(TypographyRole.SANS, 32)

        self.assertTrue(hasattr(font, "getbbox"))

    def test_text_wrapping_respects_content_width(self) -> None:
        resolver = FontResolver()
        font = resolver.font(TypographyRole.SANS, 30)
        image = Image.new("RGB", (400, 400))
        draw = ImageDraw.Draw(image)
        lines = wrap_text("This is a deliberately long headline for wrapping.", font, 220, draw)

        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(draw.textbbox((0, 0), line, font=font)[2], 220)

    def test_long_headline_does_not_render_outside_safe_bounds(self) -> None:
        renderer = RoboticsDemoRenderer()
        style = StyleResolver().resolve(
            domain="robotics",
            content_style=ContentStyle.DYNAMIC_TECH,
            editorial_tone=EditorialTone.NEUTRAL,
        )

        self.assertTrue(
            headline_within_safe_bounds(
                renderer,
                style,
                "Robots are learning to understand natural-language instructions.",
            )
        )

    def test_styles_resolve_differently_beyond_one_color(self) -> None:
        resolver = StyleResolver()
        dynamic = resolver.resolve(
            domain="robotics",
            content_style=ContentStyle.DYNAMIC_TECH,
            editorial_tone=EditorialTone.NEUTRAL,
        )
        editorial = resolver.resolve(
            domain="robotics",
            content_style=ContentStyle.EDITORIAL_HUMAN,
            editorial_tone=EditorialTone.NEUTRAL,
        )

        differences = [
            dynamic.background != editorial.background,
            dynamic.surface != editorial.surface,
            dynamic.accent != editorial.accent,
            dynamic.headline_role != editorial.headline_role,
            dynamic.marker != editorial.marker,
        ]
        self.assertGreaterEqual(sum(differences), 4)

    def test_renderer_can_render_all_major_scene_layouts(self) -> None:
        renderer = RoboticsDemoRenderer()
        style = StyleResolver().resolve(
            domain="robotics",
            content_style=ContentStyle.EDITORIAL_HUMAN,
            editorial_tone=EditorialTone.NEUTRAL,
        )

        for scene_number in range(1, 5):
            frame = renderer.render_scene(
                scene_number,
                style=style,
                content=DemoContent(),
                subtitle="Short subtitle",
            )
            self.assertEqual(frame.size, (1080, 1920))

    def test_arbitrary_series_labels_and_domains_work(self) -> None:
        renderer = RoboticsDemoRenderer()
        content = DemoContent(domain="farming", series_label="AI x FARMING")
        with tempfile.TemporaryDirectory() as directory:
            paths = renderer.render_stills(
                content_style=ContentStyle.DYNAMIC_TECH,
                preview_dir=Path(directory),
                content=content,
            )

        self.assertEqual(len(paths), 4)

    def test_subtitle_positioning_respects_safe_zones(self) -> None:
        style = StyleResolver().resolve(
            domain="education",
            content_style=ContentStyle.EDITORIAL_HUMAN,
            editorial_tone=EditorialTone.NEUTRAL,
        )
        image = Image.new("RGB", (1080, 1920), style.background)
        draw = ImageDraw.Draw(image)
        font = FontResolver().font(TypographyRole.SANS, 42)
        box = draw_subtitle(draw, "Alongside people", font, style, style.safe_zone)

        self.assertTrue(assert_box_inside_safe_zone(box, style.safe_zone))

    def test_hook_emphasis_does_not_overlap_text_glyph_area(self) -> None:
        renderer = RoboticsDemoRenderer()
        style = StyleResolver().resolve(
            domain="robotics",
            content_style=ContentStyle.EDITORIAL_HUMAN,
            editorial_tone=EditorialTone.NEUTRAL,
        )
        text_box, underline_box = hook_emphasis_boxes(renderer, style)

        self.assertGreater(underline_box[1], text_box[3])

    def test_scene_style_override_works(self) -> None:
        renderer = RoboticsDemoRenderer()
        presentation = ScenePresentation(
            scene_number=2,
            subtitle="Vision plus language",
            preview_name="scene.png",
            style_override=ContentStyle.DYNAMIC_TECH,
        )

        style = renderer.resolve_scene_style(
            domain="robotics",
            global_style=ContentStyle.EDITORIAL_HUMAN,
            presentation=presentation,
        )

        self.assertIn("dynamic_tech", style.name)

    def test_scene_without_override_inherits_global_style(self) -> None:
        renderer = RoboticsDemoRenderer()
        presentation = ScenePresentation(
            scene_number=1,
            subtitle="Robots are learning",
            preview_name="scene.png",
        )

        style = renderer.resolve_scene_style(
            domain="robotics",
            global_style=ContentStyle.EDITORIAL_HUMAN,
            presentation=presentation,
        )

        self.assertIn("editorial_human", style.name)

    def test_hybrid_video_can_contain_multiple_existing_styles(self) -> None:
        overrides = {scene.style_override for scene in HYBRID_SCENES}

        self.assertIn(ContentStyle.DYNAMIC_TECH, overrides)
        self.assertIn(ContentStyle.EDITORIAL_HUMAN, overrides)

    def test_outro_retains_fixed_brand_treatment(self) -> None:
        content = DemoContent()

        self.assertEqual(content.outro, "AI × EVERYTHING")
        self.assertEqual(content.outro_line, "Understand what's changing.")
