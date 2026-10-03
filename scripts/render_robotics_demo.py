from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rendering.robotics_demo import HYBRID_SCENES, RoboticsDemoRenderer
from src.rendering.style import ContentStyle


def main() -> None:
    renderer = RoboticsDemoRenderer()
    renderer.render_video(
        content_style=ContentStyle.DYNAMIC_TECH,
        preview_dir=Path("output/previews/robotics_dynamic_tech"),
        output_path=Path("output/videos/robotics_dynamic_tech.mp4"),
    )
    renderer.render_video(
        content_style=ContentStyle.EDITORIAL_HUMAN,
        preview_dir=Path("output/previews/robotics_editorial_human"),
        output_path=Path("output/videos/robotics_editorial_human.mp4"),
    )
    renderer.render_video(
        content_style=ContentStyle.EDITORIAL_HUMAN,
        preview_dir=Path("output/previews/robotics_hybrid"),
        output_path=Path("output/videos/robotics_hybrid.mp4"),
        scenes=HYBRID_SCENES,
    )


if __name__ == "__main__":
    main()
