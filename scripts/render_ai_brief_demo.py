from datetime import date
from pathlib import Path
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.editorial.formats import AIBriefItem, AIBriefPackage, BriefSourceRef, FormatValidationResult
from src.rendering.carousel.models import (
    CANVAS,
    CarouselVariant,
    CropStrategy,
    HumanVisualSelection,
    MediaAsset,
    MediaAssetType,
    MediaRightsStatus,
    MediaSourceType,
    VisualRole,
)
from src.rendering.carousel.renderer import AIBriefCarouselRenderer


OUTPUT_ROOT = ROOT / "output" / "carousels"
MEDIA_ROOT = ROOT / "output" / "media" / "demo"


def main() -> None:
    package = _production_demo_package()
    media_assets = _ensure_demo_media()
    selections = _visual_selections()
    output_dir = OUTPUT_ROOT / "ai_brief_production_demo"
    _prepare_output_dir(output_dir)
    rendered = AIBriefCarouselRenderer().render(
        package,
        variant=CarouselVariant.EDITORIAL,
        output_dir=output_dir,
        visual_selections=selections,
        media_assets=media_assets,
        production=True,
    )
    _verify_dimensions(rendered.slide_paths)
    print("EVERYTHING × AI")
    print("AI BRIEF PRODUCTION DEMO")
    print("Network calls: 0")
    print("LLM/API calls: 0")
    print()
    print(f"Brief: {package.subtitle}")
    print(f"Items: {package.item_count}")
    print(f"Output: {output_dir}")
    print(f"Slides: {len(rendered.slide_paths)}")
    print(f"Contact sheet: {rendered.contact_sheet_path}")
    print(f"QA: {rendered.qa_status.value.upper()}")
    for message in rendered.qa_messages:
        print(f"- {message}")


def _production_demo_package() -> AIBriefPackage:
    items = [
        _item(
            1,
            "demo-research",
            "research",
            "Fictional lab reports a smaller model benchmark",
            "DEMO ONLY: A fictional research team says a compact model matched a narrow evaluation while using fewer compute steps in a controlled test.",
            "The useful angle is not the benchmark itself; it is the pressure toward cheaper, more specialized AI systems when the task is well bounded.",
        ),
        _item(
            2,
            "demo-robotics",
            "robotics",
            "Fictional robotics pilot adds vision checks to assembly",
            "DEMO ONLY: A fictional manufacturer supplied approved pilot imagery showing robot arms inspecting a repeated station before human review.",
            "The workflow story is about verification: AI assists the inspection loop, but the demo does not claim autonomous factory replacement.",
        ),
        _item(
            3,
            "demo-healthcare",
            "healthcare",
            "Fictional clinic validates an AI triage queue",
            "DEMO ONLY: A fictional clinic describes a limited validation step where staff used an AI queue to prioritize non-emergency review.",
            "Healthcare adoption depends on evidence, governance, and human oversight; a validated queue is different from automated diagnosis.",
        ),
        _item(
            4,
            "demo-chips",
            "chips",
            "Fictional accelerator board targets lower inference cost",
            "DEMO ONLY: A fictional hardware release says the board is designed for inference workloads and cites a 30% lab efficiency target.",
            "Infrastructure changes matter when they reduce serving costs, but the number remains a demo claim tied only to this fictional fixture.",
        ),
        _item(
            5,
            "demo-policy",
            "policy",
            "Fictional workforce guidance shifts from bans to review",
            "DEMO ONLY: A fictional policy memo moves teams from blanket AI bans toward approved-use lists, disclosure rules, and periodic review.",
            "The shift signals a more mature phase: organizations are trying to manage AI work rather than simply block or hype it.",
        ),
    ]
    return AIBriefPackage(
        brief_id="demo-ai-brief-production-carousel",
        date=date(2026, 10, 3),
        title="The AI Brief",
        subtitle="5 AI developments worth knowing today",
        items=items,
        validation=FormatValidationResult(ready=True),
    )


def _item(position: int, story_id: str, category: str, headline: str, what: str, why: str) -> AIBriefItem:
    return AIBriefItem(
        position=position,
        story_id=story_id,
        cluster_id=story_id,
        headline=headline,
        category=category,
        what_happened=what,
        why_it_matters=why,
        supporting_claim_ids=[f"{story_id}-claim"],
        evidence_reference_ids=[f"{story_id}-evidence"],
        source_refs=[
            BriefSourceRef(
                story_id=story_id,
                source_id=f"{story_id}-source",
                source_name="Fictional Demo Source",
                source_url=f"https://example.com/{story_id}",
            )
        ],
    )


def _visual_selections() -> dict[str, HumanVisualSelection]:
    return {
        "demo-research": HumanVisualSelection("demo-research", VisualRole.EXPLAINER_DIAGRAM, use_diagram=True),
        "demo-robotics": HumanVisualSelection("demo-robotics", VisualRole.SOURCE_MEDIA, selected_asset_id="robotics-demo-source"),
        "demo-healthcare": HumanVisualSelection("demo-healthcare", VisualRole.LICENSED_MEDIA, selected_asset_id="healthcare-demo-licensed"),
        "demo-chips": HumanVisualSelection("demo-chips", VisualRole.EDITORIAL_GRAPHIC),
        "demo-policy": HumanVisualSelection("demo-policy", VisualRole.TYPOGRAPHY, use_typography=True),
    }


def _ensure_demo_media() -> dict[str, MediaAsset]:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    robotics = MEDIA_ROOT / "robotics_source_placeholder.jpg"
    healthcare = MEDIA_ROOT / "healthcare_licensed_placeholder.jpg"
    _placeholder_image(robotics, "APPROVED SOURCE MEDIA", (197, 88, 60), (28, 31, 34))
    _placeholder_image(healthcare, "LICENSED MEDIA MOCK", (52, 132, 117), (244, 241, 234))
    return {
        "robotics-demo-source": MediaAsset(
            asset_id="robotics-demo-source",
            story_id="demo-robotics",
            asset_type=MediaAssetType.IMAGE,
            source_type=MediaSourceType.LOCAL_DEMO,
            source_url="local-demo://robotics",
            original_url="local-demo://robotics",
            local_path=robotics,
            mime_type="image/jpeg",
            width=1400,
            height=900,
            license_status=MediaRightsStatus.APPROVED,
            license_name="editor-approved-demo",
            crop_strategy=CropStrategy.CENTER,
            visual_role=VisualRole.SOURCE_MEDIA,
        ),
        "healthcare-demo-licensed": MediaAsset(
            asset_id="healthcare-demo-licensed",
            story_id="demo-healthcare",
            asset_type=MediaAssetType.IMAGE,
            source_type=MediaSourceType.LOCAL_DEMO,
            source_url="local-demo://healthcare",
            original_url="local-demo://healthcare",
            local_path=healthcare,
            mime_type="image/jpeg",
            width=1400,
            height=900,
            license_status=MediaRightsStatus.ATTRIBUTION_REQUIRED,
            license_name="fictional-demo-license",
            attribution_required=True,
            attribution_text="Fictional licensed demo image",
            crop_strategy=CropStrategy.CENTER,
            visual_role=VisualRole.LICENSED_MEDIA,
        ),
    }


def _placeholder_image(path: Path, label: str, accent: tuple[int, int, int], background: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (1400, 900), background)
    draw = ImageDraw.Draw(image)
    for index in range(0, 1400, 90):
        draw.line((index, 0, index - 260, 900), fill=accent, width=2)
    draw.rectangle((110, 110, 1290, 790), outline=accent, width=10)
    draw.rectangle((170, 640, 820, 690), fill=accent)
    draw.text((170, 180), label, fill=accent)
    image.save(path, quality=92)


def _prepare_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("slide_*.png", "contact_sheet.png"):
        for path in output_dir.glob(pattern):
            path.unlink()


def _verify_dimensions(paths: list[Path]) -> None:
    for path in paths:
        with Image.open(path) as image:
            if image.size != (CANVAS.width, CANVAS.height):
                raise RuntimeError(f"{path} has unexpected dimensions {image.size}")


if __name__ == "__main__":
    main()
