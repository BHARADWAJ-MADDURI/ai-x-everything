from dataclasses import replace
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp
import unittest

from PIL import Image

from src.editorial.formats import AIBriefItem, AIBriefPackage, BriefSourceRef, FormatValidationResult
from src.rendering.carousel.director import AIBriefCarouselDirector
from src.rendering.carousel.grounded_visuals import validate_diagram_spec, validate_editorial_graphic
from src.rendering.carousel.layouts import production_layout_for_slide
from src.rendering.carousel.media import (
    MediaCache,
    MediaDownloadError,
    PexelsMediaProvider,
    cap_candidates,
    is_safe_media_url,
    media_search_query,
    normalize_image,
    preserve_human_selection,
    validate_media_asset,
    visual_role_for_story,
)
from src.rendering.carousel.models import (
    CANVAS,
    CarouselQAStatus,
    CarouselSlide,
    CarouselSlideType,
    CarouselVariant,
    CropStrategy,
    DiagramEdge,
    DiagramNode,
    DiagramSpec,
    EditorialComposition,
    EditorialGraphicSpec,
    FocalPoint,
    HumanVisualSelection,
    MediaAsset,
    MediaAssetType,
    MediaCandidate,
    MediaRightsStatus,
    MediaSourceType,
    VisualRole,
)
from src.rendering.carousel.qa import qa_grounded_visuals, qa_slide_media, qa_slides
from src.rendering.carousel.renderer import AIBriefCarouselRenderer, _with_production_composition


class CarouselMediaArtDirectionTests(unittest.TestCase):
    def test_visual_roles_defined(self) -> None:
        self.assertEqual({role.value for role in VisualRole}, {
            "source_media",
            "licensed_media",
            "explainer_diagram",
            "editorial_graphic",
            "typography",
        })

    def test_source_media_supported(self) -> None:
        self.assertEqual(visual_role_for_story(domain="robotics", has_media=True), VisualRole.SOURCE_MEDIA)

    def test_licensed_media_supported(self) -> None:
        asset = _asset(license_status=MediaRightsStatus.ATTRIBUTION_REQUIRED, attribution_required=True, attribution_text="Provider / Photographer")
        allowed, issues = validate_media_asset(asset)
        self.assertTrue(allowed)
        self.assertEqual(issues, [])

    def test_explainer_diagram_supported(self) -> None:
        self.assertEqual(visual_role_for_story(domain="research model"), VisualRole.EXPLAINER_DIAGRAM)

    def test_editorial_graphic_supported(self) -> None:
        self.assertEqual(visual_role_for_story(domain="chips infrastructure"), VisualRole.EDITORIAL_GRAPHIC)

    def test_typography_supported(self) -> None:
        self.assertEqual(visual_role_for_story(domain="policy workforce"), VisualRole.TYPOGRAPHY)

    def test_typography_valid_when_no_media_exists(self) -> None:
        slide = _slide(visual_role=VisualRole.TYPOGRAPHY)
        status, messages = qa_slide_media(slide)
        self.assertEqual(status, CarouselQAStatus.PASS)
        self.assertEqual(messages, [])

    def test_unknown_rights_media_blocked(self) -> None:
        allowed, issues = validate_media_asset(_asset(license_status=MediaRightsStatus.UNKNOWN))
        self.assertFalse(allowed)
        self.assertTrue(any("blocked" in issue for issue in issues))

    def test_rejected_media_blocked(self) -> None:
        allowed, issues = validate_media_asset(_asset(license_status=MediaRightsStatus.REJECTED))
        self.assertFalse(allowed)
        self.assertTrue(any("blocked" in issue for issue in issues))

    def test_approved_media_allowed(self) -> None:
        allowed, _ = validate_media_asset(_asset())
        self.assertTrue(allowed)

    def test_attribution_required_media_allowed_with_attribution(self) -> None:
        slide = _slide(
            visual_role=VisualRole.LICENSED_MEDIA,
            media_asset=_asset(license_status=MediaRightsStatus.ATTRIBUTION_REQUIRED, attribution_required=True, attribution_text="Provider / Photographer"),
            media_attribution="Provider / Photographer",
        )
        status, _ = qa_slide_media(slide)
        self.assertEqual(status, CarouselQAStatus.PASS)

    def test_attribution_required_media_fails_without_attribution_text(self) -> None:
        allowed, issues = validate_media_asset(_asset(license_status=MediaRightsStatus.ATTRIBUTION_REQUIRED, attribution_required=True, attribution_text=None))
        self.assertFalse(allowed)
        self.assertTrue(any("attribution" in issue for issue in issues))

    def test_story_source_is_not_media_source(self) -> None:
        slide = _slide(visual_role=VisualRole.SOURCE_MEDIA, media_asset=_asset(source_url="https://media.example/image.jpg"))
        self.assertNotEqual(slide.source_label, slide.media_asset.source_url)

    def test_candidate_list_supports_up_to_three(self) -> None:
        candidates = [_candidate(rank) for rank in range(5)]
        self.assertEqual(len(cap_candidates(candidates)), 3)

    def test_human_selection_preserved(self) -> None:
        candidates = [_candidate(2), _candidate(1)]
        selected = preserve_human_selection("asset-2", candidates)
        self.assertEqual(selected.asset.asset_id, "asset-2")

    def test_no_first_result_auto_approval(self) -> None:
        self.assertFalse(_candidate(1).approved_for_render)

    def test_url_safety_allows_public_https(self) -> None:
        self.assertTrue(is_safe_media_url("https://example.com/image.jpg"))

    def test_private_ip_rejected(self) -> None:
        self.assertFalse(is_safe_media_url("http://192.168.1.10/image.jpg"))

    def test_unsafe_localhost_rejected(self) -> None:
        self.assertFalse(is_safe_media_url("http://localhost/image.jpg"))

    def test_oversized_download_rejected(self) -> None:
        cache = MediaCache(Path(self._tmp.name), max_bytes=8, transport=lambda *_: (b"x" * 9, "image/jpeg"))
        with self.assertRaises(MediaDownloadError):
            cache.fetch_original(_asset(original_url="https://example.com/large.jpg", local_path=None))

    def test_unsupported_content_type_rejected(self) -> None:
        cache = MediaCache(Path(self._tmp.name), transport=lambda *_: (b"hello", "text/html"))
        with self.assertRaises(MediaDownloadError):
            cache.fetch_original(_asset(original_url="https://example.com/page", local_path=None))

    def test_malformed_image_rejected(self) -> None:
        cache = MediaCache(Path(self._tmp.name), transport=lambda *_: (b"not-an-image", "image/jpeg"))
        with self.assertRaises(MediaDownloadError):
            cache.fetch_original(_asset(original_url="https://example.com/bad.jpg", local_path=None))

    def test_cache_prevents_repeat_download(self) -> None:
        calls = {"count": 0}

        def transport(*_):
            calls["count"] += 1
            return _jpeg_bytes(900, 700), "image/jpeg"

        cache = MediaCache(Path(self._tmp.name), transport=transport)
        asset = _asset(original_url="https://example.com/cached.jpg", local_path=None)
        cache.fetch_original(asset)
        cache.fetch_original(asset)
        self.assertEqual(calls["count"], 1)

    def test_original_preserved(self) -> None:
        cache = MediaCache(Path(self._tmp.name), transport=lambda *_: (_jpeg_bytes(900, 700), "image/jpeg"))
        fetched = cache.fetch_original(_asset(original_url="https://example.com/original.jpg", local_path=None))
        self.assertTrue(fetched.local_path.exists())
        self.assertEqual(fetched.local_path.name, "original.jpg")

    def test_normalized_derivative_created(self) -> None:
        cache = MediaCache(Path(self._tmp.name))
        derivative = cache.normalize(_asset(width=900, height=700), width=300, height=200)
        self.assertTrue(derivative.exists())

    def test_aspect_ratio_preserved(self) -> None:
        image = Image.new("RGB", (800, 400), (200, 10, 10))
        normalized = normalize_image(image, target_size=(300, 300), crop_strategy=CropStrategy.CONTAIN)
        self.assertEqual(normalized.size, (300, 300))

    def test_center_crop(self) -> None:
        self.assertEqual(normalize_image(_wide_image(), target_size=(200, 200), crop_strategy=CropStrategy.CENTER).size, (200, 200))

    def test_top_crop(self) -> None:
        self.assertEqual(normalize_image(_tall_image(), target_size=(200, 200), crop_strategy=CropStrategy.TOP).size, (200, 200))

    def test_bottom_crop(self) -> None:
        self.assertEqual(normalize_image(_tall_image(), target_size=(200, 200), crop_strategy=CropStrategy.BOTTOM).size, (200, 200))

    def test_left_crop(self) -> None:
        self.assertEqual(normalize_image(_wide_image(), target_size=(200, 200), crop_strategy=CropStrategy.LEFT).size, (200, 200))

    def test_right_crop(self) -> None:
        self.assertEqual(normalize_image(_wide_image(), target_size=(200, 200), crop_strategy=CropStrategy.RIGHT).size, (200, 200))

    def test_contain(self) -> None:
        self.assertEqual(normalize_image(_wide_image(), target_size=(250, 250), crop_strategy=CropStrategy.CONTAIN).size, (250, 250))

    def test_minimum_resolution_rejection(self) -> None:
        cache = MediaCache(Path(self._tmp.name), transport=lambda *_: (_jpeg_bytes(200, 120), "image/jpeg"))
        with self.assertRaises(MediaDownloadError):
            cache.fetch_original(_asset(original_url="https://example.com/small.jpg", local_path=None))

    def test_no_extreme_upscale(self) -> None:
        cache = MediaCache(Path(self._tmp.name))
        with self.assertRaises(MediaDownloadError):
            cache.normalize(_asset(width=100, height=80), width=600, height=500)

    def test_diagram_requires_supporting_claim_refs(self) -> None:
        ok, issues = validate_diagram_spec(DiagramSpec("story", [], [], []), {"claim-1"})
        self.assertFalse(ok)
        self.assertTrue(any("requires" in issue for issue in issues))

    def test_invalid_diagram_claim_ref_rejected(self) -> None:
        ok, issues = validate_diagram_spec(_diagram(["unknown"]), {"claim-1"})
        self.assertFalse(ok)
        self.assertTrue(any("invalid claim" in issue for issue in issues))

    def test_unsupported_diagram_relationship_rejected(self) -> None:
        spec = DiagramSpec(
            "story",
            [DiagramNode("a", "A", ["claim-1"]), DiagramNode("b", "B", ["claim-1"])],
            [DiagramEdge("a", "b", "dominates", ["claim-1"])],
            ["claim-1"],
        )
        ok, issues = validate_diagram_spec(spec, {"claim-1"})
        self.assertFalse(ok)
        self.assertTrue(any("unsupported" in issue for issue in issues))

    def test_numeric_graphic_requires_verified_numeric_claim(self) -> None:
        ok, issues = validate_editorial_graphic(EditorialGraphicSpec("story", "number", "Efficiency", "30%", ["claim-1"]), "verified 30% target")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_unsupported_number_rejected(self) -> None:
        ok, issues = validate_editorial_graphic(EditorialGraphicSpec("story", "number", "Efficiency", "40%", ["claim-1"]), "verified 30% target")
        self.assertFalse(ok)
        self.assertTrue(any("unsupported numeric" in issue for issue in issues))

    def test_photo_dominant_layout(self) -> None:
        self.assertEqual(_production_slide(VisualRole.SOURCE_MEDIA).layout_composition, EditorialComposition.PHOTO_DOMINANT)

    def test_text_editorial_layout(self) -> None:
        self.assertEqual(_production_slide(VisualRole.TYPOGRAPHY, category="research").layout_composition, EditorialComposition.TEXT_EDITORIAL)

    def test_diagram_layout(self) -> None:
        self.assertEqual(_production_slide(VisualRole.EXPLAINER_DIAGRAM).layout_composition, EditorialComposition.DIAGRAM_EXPLAINER)

    def test_data_editorial_layout(self) -> None:
        self.assertEqual(_production_slide(VisualRole.EDITORIAL_GRAPHIC).layout_composition, EditorialComposition.DATA_EDITORIAL)

    def test_document_policy_layout(self) -> None:
        self.assertEqual(_production_slide(VisualRole.TYPOGRAPHY, category="policy").layout_composition, EditorialComposition.DOCUMENT_POLICY)

    def test_neutral_fallback_layout(self) -> None:
        layout = production_layout_for_slide(_slide(visual_role=VisualRole.TYPOGRAPHY, category="general"))
        self.assertEqual(layout.visual_box, (CANVAS.safe_left, 1075, CANVAS.safe_right, 1125))

    def test_cover_shows_actual_item_count(self) -> None:
        slides = AIBriefCarouselDirector().build_slides(_package(), CarouselVariant.EDITORIAL)
        self.assertEqual(slides[0].subtitle, "5 AI developments worth knowing today")

    def test_cover_shows_fitted_story_teasers(self) -> None:
        slides = AIBriefCarouselDirector().build_slides(_package(), CarouselVariant.EDITORIAL)
        self.assertEqual(len(slides[0].teasers), 5)
        self.assertTrue(all(len(teaser) <= 58 for teaser in slides[0].teasers))

    def test_realistic_text_wrapping_production_render(self) -> None:
        rendered = _render_production(self._tmp_path)
        self.assertEqual(len(rendered.slide_paths), 7)

    def test_source_attribution_visible(self) -> None:
        rendered = _render_production(self._tmp_path)
        self.assertTrue(any("SOURCE" in region.text for region in _story_regions(rendered.output_dir)))

    def test_required_media_attribution_visible(self) -> None:
        package = _package()
        asset = _asset(asset_id="licensed", story_id=package.items[1].story_id, license_status=MediaRightsStatus.ATTRIBUTION_REQUIRED, attribution_required=True, attribution_text="Provider / Person")
        selections = {package.items[1].story_id: HumanVisualSelection(package.items[1].story_id, VisualRole.LICENSED_MEDIA, selected_asset_id="licensed")}
        rendered = AIBriefCarouselRenderer().render(
            package,
            variant=CarouselVariant.EDITORIAL,
            output_dir=self._tmp_path / "attribution",
            visual_selections=selections,
            media_assets={"licensed": asset},
            production=True,
        )
        self.assertEqual(rendered.qa_status, CarouselQAStatus.PASS)

    def test_offline_demo_performs_zero_network_calls(self) -> None:
        self.assertEqual(PexelsMediaProvider(api_key=None).search("robotics"), [])

    def test_unit_tests_perform_zero_network_calls(self) -> None:
        cache = MediaCache(Path(self._tmp.name), transport=lambda *_: (_jpeg_bytes(900, 700), "image/jpeg"))
        fetched = cache.fetch_original(_asset(original_url="https://example.com/offline.jpg", local_path=None))
        self.assertTrue(fetched.local_path.exists())

    def test_no_llm_calls(self) -> None:
        self.assertFalse(hasattr(AIBriefCarouselRenderer(), "llm_client"))

    def test_previous_carousel_tests_remain_green_contract(self) -> None:
        rendered = AIBriefCarouselRenderer().render(_package(), variant=CarouselVariant.EDITORIAL, output_dir=self._tmp_path / "legacy")
        self.assertEqual(rendered.qa_status, CarouselQAStatus.PASS)

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()


def _asset(
    *,
    asset_id: str = "asset-1",
    story_id: str = "story-1",
    source_url: str = "https://provider.example/image.jpg",
    original_url: str = "https://provider.example/image.jpg",
    local_path: Path | None | str = "auto",
    width: int = 900,
    height: int = 700,
    license_status: MediaRightsStatus = MediaRightsStatus.APPROVED,
    attribution_required: bool = False,
    attribution_text: str | None = None,
) -> MediaAsset:
    if local_path == "auto":
        path = Path(mkdtemp(prefix="carousel-media-test-")) / "asset.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (width, height), (20, 120, 160)).save(path)
    else:
        path = local_path
    return MediaAsset(
        asset_id=asset_id,
        story_id=story_id,
        asset_type=MediaAssetType.IMAGE,
        source_type=MediaSourceType.LICENSED_PROVIDER,
        source_url=source_url,
        original_url=original_url,
        local_path=Path(path) if path else None,
        mime_type="image/jpeg",
        width=width,
        height=height,
        license_status=license_status,
        attribution_required=attribution_required,
        attribution_text=attribution_text,
        crop_strategy=CropStrategy.CENTER,
        focal_point=FocalPoint(),
        visual_role=VisualRole.LICENSED_MEDIA,
    )


def _candidate(rank: int) -> MediaCandidate:
    return MediaCandidate(asset=_asset(asset_id=f"asset-{rank}"), relevance_note="grounded candidate", rank=rank)


def _slide(
    *,
    visual_role: VisualRole,
    category: str = "robotics",
    media_asset: MediaAsset | None = None,
    media_attribution: str | None = None,
) -> CarouselSlide:
    item = _package().items[0]
    return CarouselSlide(
        position=2,
        slide_type=CarouselSlideType.STORY,
        variant=CarouselVariant.EDITORIAL,
        title=item.headline,
        item=item,
        category=category,
        source_label="SOURCE · FICTIONAL DEMO SOURCE",
        visual_role=visual_role,
        media_asset=media_asset,
        media_attribution=media_attribution,
    )


def _production_slide(role: VisualRole, category: str = "robotics") -> CarouselSlide:
    return _with_production_composition(_slide(visual_role=role, category=category))


def _diagram(claim_ids: list[str]) -> DiagramSpec:
    return DiagramSpec(
        "story",
        [DiagramNode("a", "A", claim_ids), DiagramNode("b", "B", claim_ids)],
        [DiagramEdge("a", "b", "supports", claim_ids)],
        claim_ids,
    )


def _package() -> AIBriefPackage:
    items = [
        AIBriefItem(
            position=index,
            story_id=f"story-{index}",
            cluster_id=f"story-{index}",
            headline=f"Fictional AI story {index} has enough copy for wrapping",
            category=["research", "robotics", "healthcare", "chips", "policy"][index - 1],
            what_happened=f"DEMO ONLY: Fictional development {index} includes enough context to test line wrapping and presentation hierarchy.",
            why_it_matters=f"DEMO ONLY: The importance of story {index} is distinct from the setup and explains the practical editorial angle.",
            supporting_claim_ids=[f"story-{index}-claim"],
            evidence_reference_ids=[f"story-{index}-evidence"],
            source_refs=[BriefSourceRef(f"story-{index}", f"source-{index}", "Fictional Demo Source", f"https://example.com/story-{index}")],
        )
        for index in range(1, 6)
    ]
    return AIBriefPackage(
        brief_id="brief",
        date=__import__("datetime").date(2026, 10, 3),
        title="The AI Brief",
        subtitle="5 AI developments worth knowing today",
        items=items,
        validation=FormatValidationResult(ready=True),
    )


def _render_production(tmp_path: Path):
    package = _package()
    asset = _asset(asset_id="media", story_id="story-2")
    selections = {"story-2": HumanVisualSelection("story-2", VisualRole.SOURCE_MEDIA, selected_asset_id="media")}
    return AIBriefCarouselRenderer().render(
        package,
        variant=CarouselVariant.EDITORIAL,
        output_dir=tmp_path / "production",
        visual_selections=selections,
        media_assets={"media": asset},
        production=True,
    )


def _story_regions(_output_dir: Path):
    package = _package()
    rendered_slide, _ = AIBriefCarouselRenderer()._render_slide(
        AIBriefCarouselDirector().build_slides(package, CarouselVariant.EDITORIAL)[1],
        package,
        production=True,
    )
    return rendered_slide.text_regions


def _jpeg_bytes(width: int, height: int) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _wide_image() -> Image.Image:
    return Image.new("RGB", (600, 240), (100, 20, 20))


def _tall_image() -> Image.Image:
    return Image.new("RGB", (240, 600), (20, 100, 20))


if __name__ == "__main__":
    unittest.main()
