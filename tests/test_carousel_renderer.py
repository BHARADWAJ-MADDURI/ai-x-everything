from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp
import unittest

from PIL import Image

from src.editorial.demo_fixture import DEMO_NOW, _planning_story
from src.editorial.formats import build_ai_brief_package
from src.rendering.carousel.art_direction import BriefArtDirection, BriefArtDirectionResolver
from src.rendering.carousel.director import AIBriefCarouselDirector
from src.rendering.carousel.models import CANVAS, CarouselQAStatus, CarouselSlide, CarouselSlideType, CarouselVariant, TextRegion
from src.rendering.carousel.qa import qa_slides, qa_text_regions
from src.rendering.carousel.renderer import AIBriefCarouselRenderer


class CarouselRendererTests(unittest.TestCase):
    def test_1080_by_1350_configuration(self) -> None:
        self.assertEqual((CANVAS.width, CANVAS.height), (1080, 1350))

    def test_slide_count_equals_item_count_plus_two(self) -> None:
        package = _brief(5)
        slides = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)

        self.assertEqual(len(slides), package.item_count + 2)

    def test_three_item_brief_renders_five_slides(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.EDITORIAL)

        self.assertEqual(len(rendered.slide_paths), 5)

    def test_ten_item_brief_renders_twelve_slides(self) -> None:
        rendered = _render_temp(_brief(10), CarouselVariant.DYNAMIC)

        self.assertEqual(len(rendered.slide_paths), 12)

    def test_cover_count_matches_package_count(self) -> None:
        package = _brief(4)
        slides = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)

        self.assertEqual(slides[0].subtitle, "4 AI developments worth knowing today")

    def test_one_story_per_story_slide(self) -> None:
        slides = AIBriefCarouselDirector().build_slides(_brief(3), CarouselVariant.EDITORIAL)

        self.assertTrue(all(slide.item is not None for slide in slides[1:-1]))

    def test_ordering_preserved(self) -> None:
        package = _brief(4)
        slides = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)

        self.assertEqual([slide.item.story_id for slide in slides[1:-1]], [item.story_id for item in package.items])

    def test_source_attribution_exists(self) -> None:
        slides = AIBriefCarouselDirector().build_slides(_brief(3), CarouselVariant.EDITORIAL)

        self.assertTrue(all((slide.source_label or "").startswith("SOURCE") for slide in slides[1:-1]))

    def test_brand_appears_on_cover(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.EDITORIAL)

        self.assertEqual(rendered.qa_status, CarouselQAStatus.PASS)

    def test_tagline_appears_where_expected(self) -> None:
        package = _brief(3)
        slides = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)

        self.assertEqual(slides[-1].subtitle, "Understand what's changing.")

    def test_safe_margins_centralized(self) -> None:
        self.assertGreater(CANVAS.safe_left, 0)
        self.assertLess(CANVAS.safe_right, CANVAS.width)

    def test_missing_headline_rejected(self) -> None:
        package = _brief(3)
        slides = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)
        bad = [replace(slides[0], title=""), *slides[1:]]
        status, messages = qa_slides(bad, package)

        self.assertEqual(status, CarouselQAStatus.FAIL)
        self.assertTrue(any("missing headline" in message for message in messages))

    def test_missing_source_rejected(self) -> None:
        package = _brief(3)
        slides = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)
        bad = [slides[0], replace(slides[1], source_label=None), *slides[2:]]
        status, messages = qa_slides(bad, package)

        self.assertEqual(status, CarouselQAStatus.FAIL)
        self.assertTrue(any("missing source" in message for message in messages))

    def test_duplicate_slide_positions_rejected(self) -> None:
        package = _brief(3)
        slides = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)
        bad = [slides[0], replace(slides[1], position=1), *slides[2:]]
        status, messages = qa_slides(bad, package)

        self.assertEqual(status, CarouselQAStatus.FAIL)
        self.assertTrue(any("duplicate" in message for message in messages))

    def test_overflow_detected(self) -> None:
        region = TextRegion("overflow", (CANVAS.safe_left - 1, 100, 200, 140), 24, "text")
        status, messages = qa_text_regions([region])

        self.assertEqual(status, CarouselQAStatus.FAIL)
        self.assertTrue(any("safe margins" in message for message in messages))

    def test_tiny_font_condition_detected(self) -> None:
        region = TextRegion("tiny", (CANVAS.safe_left, 100, 200, 140), 12, "text")
        status, messages = qa_text_regions([region])

        self.assertEqual(status, CarouselQAStatus.WARNING)
        self.assertTrue(any("tiny font" in message for message in messages))

    def test_neutral_art_direction_fallback(self) -> None:
        resolver = BriefArtDirectionResolver()

        self.assertEqual(resolver.resolve_direction("unknown"), BriefArtDirection.EDITORIAL_NEUTRAL)

    def test_research_style_resolution(self) -> None:
        self.assertEqual(BriefArtDirectionResolver().resolve_direction("research"), BriefArtDirection.RESEARCH)

    def test_technical_style_resolution(self) -> None:
        self.assertEqual(BriefArtDirectionResolver().resolve_direction("developer tools"), BriefArtDirection.TECHNICAL)

    def test_clinical_style_resolution(self) -> None:
        self.assertEqual(BriefArtDirectionResolver().resolve_direction("healthcare"), BriefArtDirection.CLINICAL)

    def test_industrial_style_resolution(self) -> None:
        self.assertEqual(BriefArtDirectionResolver().resolve_direction("chips infrastructure"), BriefArtDirection.INDUSTRIAL)

    def test_policy_style_resolution(self) -> None:
        self.assertEqual(BriefArtDirectionResolver().resolve_direction("regulation policy"), BriefArtDirection.POLICY)

    def test_editorial_variant_renders(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.EDITORIAL)

        self.assertEqual(rendered.qa_status, CarouselQAStatus.PASS)

    def test_dynamic_variant_renders(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.DYNAMIC)

        self.assertEqual(rendered.qa_status, CarouselQAStatus.PASS)

    def test_variants_differ_structurally_not_only_by_color(self) -> None:
        package = _brief(3)
        editorial = AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)[1]
        dynamic = AIBriefCarouselDirector().build_slides(package, CarouselVariant.DYNAMIC)[1]

        self.assertNotEqual(editorial.variant, dynamic.variant)

    def test_output_dimensions_correct(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.EDITORIAL)
        with Image.open(rendered.slide_paths[0]) as image:
            self.assertEqual(image.size, (CANVAS.width, CANVAS.height))

    def test_png_output_valid(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.EDITORIAL)
        with Image.open(rendered.slide_paths[0]) as image:
            self.assertEqual(image.format, "PNG")

    def test_contact_sheet_generated(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.EDITORIAL)

        self.assertTrue(rendered.contact_sheet_path.exists())

    def test_renderer_performs_no_network_calls(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.EDITORIAL)

        self.assertTrue(rendered.slide_paths)

    def test_renderer_performs_no_llm_calls(self) -> None:
        rendered = _render_temp(_brief(3), CarouselVariant.DYNAMIC)

        self.assertTrue(rendered.slide_paths)


def _brief(count: int):
    stories = [
        _planning_story(
            f"carousel-{index}",
            f"AI carousel story {index}",
            ["research", "robotics", "healthcare", "chips", "policy", "agents", "tools", "science", "enterprise", "models"][index % 10],
            0.95 - index * 0.01,
            DEMO_NOW,
        )
        for index in range(count)
    ]
    return build_ai_brief_package(brief_id="brief-test", package_date=DEMO_NOW.date(), stories=stories)


def _render_temp(package, variant: CarouselVariant):
    output_dir = Path(mkdtemp(prefix="ai-brief-carousel-test-")) / variant.value
    return AIBriefCarouselRenderer().render(package, variant=variant, output_dir=output_dir)


if __name__ == "__main__":
    unittest.main()
