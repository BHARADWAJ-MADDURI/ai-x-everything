from src.editorial.formats import AIBriefPackage
from src.rendering.carousel.models import CarouselSlide, CarouselSlideType, CarouselVariant


class AIBriefCarouselDirector:
    """Transforms a validated AI Brief into ordered slide models."""

    def build_slides(self, package: AIBriefPackage, variant: CarouselVariant) -> list[CarouselSlide]:
        slides = [
            CarouselSlide(
                position=1,
                slide_type=CarouselSlideType.COVER,
                variant=variant,
                title=package.title.upper(),
                subtitle=package.subtitle,
            )
        ]
        for item in package.items:
            source = item.source_refs[0] if item.source_refs else None
            slides.append(
                CarouselSlide(
                    position=item.position + 1,
                    slide_type=CarouselSlideType.STORY,
                    variant=variant,
                    title=item.headline,
                    subtitle=item.what_happened,
                    item=item,
                    category=item.category,
                    source_label=f"SOURCE · {source.source_name.upper()}" if source else None,
                )
            )
        slides.append(
            CarouselSlide(
                position=len(package.items) + 2,
                slide_type=CarouselSlideType.OUTRO,
                variant=variant,
                title="EVERYTHING × AI",
                subtitle="Understand what's changing.",
            )
        )
        return slides
