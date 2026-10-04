from dataclasses import replace

from src.intelligence.models import CandidateItem, EvidenceItem, StoryCluster
from src.intelligence.sources import evidence_from_candidate
from src.research.extraction import ExtractedText, ExtractionQuality
from src.research.retrieval import RetrievedSource, RetrievalStatus


class EvidenceExtractor:
    """Create bounded evidence material without declaring page text to be fact."""

    def __init__(self, *, max_items_per_source: int = 3, max_chars_per_item: int = 700) -> None:
        self.max_items_per_source = max_items_per_source
        self.max_chars_per_item = max_chars_per_item

    def extract(
        self,
        *,
        cluster: StoryCluster,
        candidate: CandidateItem,
        retrieved_source: RetrievedSource,
        extracted_text: ExtractedText,
        source_index: int = 1,
    ) -> list[EvidenceItem]:
        if retrieved_source.retrieval_status is not RetrievalStatus.SUCCESS:
            return []
        if extracted_text.quality is ExtractionQuality.EMPTY:
            return []
        source = replace(evidence_from_candidate(candidate), source_id=f"source_{source_index:03d}")
        chunks = _chunk_text(extracted_text.text, self.max_chars_per_item, self.max_items_per_source)
        return [
            EvidenceItem(
                evidence_id=f"{cluster.id}_retrieved_{source_index:03d}_{index:03d}",
                cluster_id=cluster.id,
                source_id=source.source_id,
                source_url=retrieved_source.final_url or candidate.source_url,
                source_type=candidate.source_type,
                supplied_text=chunk,
                published_at=candidate.published_at,
            )
            for index, chunk in enumerate(chunks, start=1)
        ]


def _chunk_text(text: str, max_chars: int, max_items: int) -> list[str]:
    sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".") if sentence.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current}. {sentence}" if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(_ensure_period(current))
            if len(chunks) >= max_items:
                return chunks
        current = sentence[:max_chars].strip()
    if current and len(chunks) < max_items:
        chunks.append(_ensure_period(current))
    return chunks[:max_items]


def _ensure_period(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else f"{text}."
