from pathlib import Path
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.editorial.demo_fixture import DEMO_NOW, _planning_story
from src.editorial.formats import build_ai_brief_package
from src.rendering.carousel.models import CANVAS, CarouselVariant
from src.rendering.carousel.renderer import AIBriefCarouselRenderer


OUTPUT_ROOT = ROOT / "output" / "carousels"


def main() -> None:
    package = build_ai_brief_package(
        brief_id="demo-ai-brief-carousel",
        package_date=DEMO_NOW.date(),
        stories=_demo_stories(),
    )
    renderer = AIBriefCarouselRenderer()
    outputs = {
        CarouselVariant.EDITORIAL: OUTPUT_ROOT / "ai_brief_editorial",
        CarouselVariant.DYNAMIC: OUTPUT_ROOT / "ai_brief_dynamic",
    }
    print("EVERYTHING × AI")
    print("AI BRIEF CAROUSEL DEMO")
    print()
    print(f"Brief: {package.subtitle}")
    print(f"Items: {package.item_count}")
    print()
    for variant, output_dir in outputs.items():
        _prepare_output_dir(output_dir)
        rendered = renderer.render(package, variant=variant, output_dir=output_dir)
        _verify_dimensions(rendered.slide_paths)
        print(f"{variant.value.upper()}")
        print(f"Output: {output_dir}")
        print(f"Slides: {len(rendered.slide_paths)}")
        print(f"Contact sheet: {rendered.contact_sheet_path}")
        print(f"QA: {rendered.qa_status.value.upper()}")
        for message in rendered.qa_messages:
            print(f"- {message}")
        print()


def _demo_stories():
    fixtures = [
        ("foundation-model", "Foundation model research update", "research", 0.96),
        ("robotics-agents", "Robotics agents move into factory workflows", "robotics", 0.94),
        ("healthcare-ai", "Healthcare AI triage study clears a validation step", "healthcare", 0.92),
        ("ai-infrastructure", "AI infrastructure chips expand training capacity", "chips", 0.9),
        ("policy-workforce", "AI workforce policy debate shifts toward deployment", "policy", 0.88),
    ]
    return [
        _planning_story(story_id, title, domain, score, DEMO_NOW)
        for story_id, title, domain, score in fixtures
    ]


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
