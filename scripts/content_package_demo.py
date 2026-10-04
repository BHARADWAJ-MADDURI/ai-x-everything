import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.content.demo_fixture import deterministic_content_package_demo


def main() -> None:
    package = deterministic_content_package_demo()
    print("EVERYTHING × AI")
    print("PUBLISHABLE CONTENT PACKAGE")
    print()
    print("STORY")
    print("-----")
    print(package.story_id)
    print()
    print("EDITORIAL")
    print("---------")
    print(f"Angle: {package.selected_angle.angle_type.value}")
    print(f"Audience: {', '.join(audience.value for audience in package.audience)}")
    print(f"Title: {package.selected_title.text}")
    print(f"Title status: {package.selected_title.verification_status.value}")
    print()
    print("GROUNDING")
    print("---------")
    print(f"Allowed claims: {', '.join(package.allowed_claim_ids)}")
    print(f"Sources: {', '.join(source.source_name for source in package.source_references)}")
    print()
    print("REEL")
    print("----")
    print(f"Hook: {package.reel.hook}")
    print(f"Duration: {package.reel.target_duration_seconds}s")
    print("Scenes:")
    for scene in package.reel.scenes:
        print(f"- {scene.scene_id}: {scene.purpose} | {scene.visual_intent.value}")
    print(f"Narration: {package.reel.narration}")
    print()
    print("INSTAGRAM")
    print("---------")
    print(f"Caption: {package.instagram.caption}")
    print(f"Hashtags: {', '.join(tag.tag for tag in package.instagram.hashtags)}")
    print()
    print("BLOG")
    print("----")
    print(f"Headline: {package.blog.headline}")
    print("Sections: What happened, How it works, Why it matters, What to watch next")
    print()
    print("LINKEDIN")
    print("--------")
    print(package.linkedin.post_copy)
    print()
    print("X")
    print("-")
    for post in package.x.posts:
        print(post)
    print()
    print("YOUTUBE SHORTS")
    print("--------------")
    print(package.youtube_shorts.title)
    print(package.youtube_shorts.description)
    print()
    print("VALIDATION")
    print("----------")
    print(f"Status: {package.validation.status.value if package.validation else 'unknown'}")
    print(f"Issues: {package.validation.issues if package.validation else []}")
    print(f"Publish ready: {package.publish_ready}")


if __name__ == "__main__":
    main()
