from datetime import datetime
import unittest

from src.shared.models import (
    Article,
    Audience,
    AudienceValue,
    ContentAsset,
    ContentFormat,
    MetricSnapshot,
    Platform,
    Publication,
    PublicationStatus,
    Source,
    Story,
    StoryScores,
    StoryType,
)


class ModelTests(unittest.TestCase):
    def test_source_can_be_instantiated(self) -> None:
        retrieved_at = datetime(2026, 10, 3, 12, 0)

        source = Source(
            id="source-1",
            url="https://example.com/ai-news",
            title="AI News",
            publisher="Example",
            published_at=None,
            retrieved_at=retrieved_at,
            source_type="article",
        )

        self.assertEqual(source.id, "source-1")
        self.assertEqual(source.retrieved_at, retrieved_at)

    def test_story_can_be_instantiated_with_core_context(self) -> None:
        first_source = Source(
            id="source-1",
            url="https://example.com/one",
            title="First source",
            publisher="Example",
            published_at=datetime(2026, 10, 1, 9, 0),
            retrieved_at=datetime(2026, 10, 3, 12, 0),
            source_type="article",
        )
        second_source = Source(
            id="source-2",
            url="https://example.com/two",
            title="Second source",
            publisher="Example",
            published_at=None,
            retrieved_at=datetime(2026, 10, 3, 12, 5),
            source_type="research",
        )
        scores = StoryScores(
            relevance=0.9,
            timeliness=0.8,
            evidence_quality=0.7,
            educational_value=0.85,
        )
        audience_value = AudienceValue(
            student=0.75,
            professional=0.9,
            enthusiast=0.8,
        )

        story = Story(
            id="story-1",
            headline="AI changes software testing",
            summary="New AI tools help teams test software faster.",
            domain="software",
            subdomain="testing",
            story_type=StoryType.IMPACT,
            audiences=[Audience.STUDENT, Audience.PROFESSIONAL],
            professions_affected=["software engineer", "QA analyst"],
            industries_affected=["technology"],
            companies=["Example AI"],
            concepts=["agentic coding", "test generation"],
            why_it_matters="It changes how teams validate software quality.",
            sources=[first_source, second_source],
            source_published_at=datetime(2026, 10, 1, 9, 0),
            discovered_at=datetime(2026, 10, 3, 12, 10),
            scores=scores,
            audience_value=audience_value,
        )

        self.assertEqual(len(story.sources), 2)
        self.assertIn(Audience.PROFESSIONAL, story.audiences)
        self.assertIn("software engineer", story.professions_affected)
        self.assertIn("agentic coding", story.concepts)
        self.assertEqual(story.scores.relevance, 0.9)
        self.assertEqual(story.audience_value.professional, 0.9)

    def test_article_can_reference_story(self) -> None:
        article = Article(
            id="article-1",
            story_id="story-1",
            title="How AI is changing software testing",
            subtitle=None,
            tldr="AI testing tools are becoming part of software workflows.",
            what_happened="A new generation of testing tools emerged.",
            how_it_works=None,
            why_it_matters="Testing work may become faster and more strategic.",
            industry_impact=None,
            career_impact="QA and engineering roles may shift toward oversight.",
            opportunities=["Faster regression testing"],
            risks_and_limitations=["Overreliance on generated tests"],
            key_concepts=["test generation"],
            source_ids=["source-1"],
            created_at=datetime(2026, 10, 3, 12, 20),
            updated_at=datetime(2026, 10, 3, 12, 20),
        )

        self.assertEqual(article.story_id, "story-1")
        self.assertEqual(article.source_ids, ["source-1"])

    def test_content_asset_can_target_multiple_platforms(self) -> None:
        asset = ContentAsset(
            id="asset-1",
            story_id="story-1",
            article_id="article-1",
            format=ContentFormat.SHORT_VIDEO,
            target_platforms=[
                Platform.INSTAGRAM,
                Platform.TIKTOK,
                Platform.YOUTUBE,
            ],
            target_audiences=[Audience.PROFESSIONAL, Audience.ENTHUSIAST],
            title="AI testing in 30 seconds",
            hook="AI is changing software testing.",
            body="Short video script",
            call_to_action="Follow for more AI explainers.",
            generation_metadata=None,
            created_at=datetime(2026, 10, 3, 12, 30),
        )

        self.assertEqual(asset.format, ContentFormat.SHORT_VIDEO)
        self.assertEqual(len(asset.target_platforms), 3)
        self.assertIn(Platform.TIKTOK, asset.target_platforms)

    def test_content_asset_can_support_multiple_publications(self) -> None:
        first_publication = Publication(
            id="publication-1",
            content_asset_id="asset-1",
            platform=Platform.INSTAGRAM,
            format=ContentFormat.SHORT_VIDEO,
            status=PublicationStatus.DRAFT,
            platform_post_id=None,
            platform_url=None,
            published_at=None,
            created_at=datetime(2026, 10, 3, 12, 40),
        )
        second_publication = Publication(
            id="publication-2",
            content_asset_id="asset-1",
            platform=Platform.TIKTOK,
            format=ContentFormat.SHORT_VIDEO,
            status=PublicationStatus.DRAFT,
            platform_post_id=None,
            platform_url=None,
            published_at=None,
            created_at=datetime(2026, 10, 3, 12, 41),
        )

        publications = [first_publication, second_publication]

        self.assertEqual({item.content_asset_id for item in publications}, {"asset-1"})
        self.assertEqual({item.platform for item in publications}, {Platform.INSTAGRAM, Platform.TIKTOK})

    def test_metric_snapshot_supports_missing_metrics(self) -> None:
        snapshot = MetricSnapshot(
            id="metric-1",
            publication_id="publication-1",
            captured_at=datetime(2026, 10, 4, 12, 0),
            hours_since_publish=24.0,
            views=1000,
        )

        self.assertEqual(snapshot.views, 1000)
        self.assertIsNone(snapshot.comments)
        self.assertIsNone(snapshot.average_watch_time_seconds)


if __name__ == "__main__":
    unittest.main()
