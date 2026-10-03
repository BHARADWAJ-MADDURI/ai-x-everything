from src.intelligence.models import CandidateItem, StoryCluster
from src.intelligence.normalize import normalize_url, title_tokens


def cluster_candidates(candidates: list[CandidateItem]) -> list[StoryCluster]:
    """Conservatively group candidates likely covering the same development."""

    clusters: list[StoryCluster] = []
    for candidate in candidates:
        matched = None
        for cluster in clusters:
            if _belongs(candidate, cluster):
                matched = cluster
                break
        if matched:
            matched.candidates.append(candidate)
        else:
            clusters.append(StoryCluster(id=f"cluster-{len(clusters) + 1}", candidates=[candidate]))
    return clusters


def _belongs(candidate: CandidateItem, cluster: StoryCluster) -> bool:
    candidate_url = normalize_url(candidate.source_url)
    candidate_tokens = title_tokens(candidate.title)
    for existing in cluster.candidates:
        if candidate_url == normalize_url(existing.source_url):
            return True
        existing_tokens = title_tokens(existing.title)
        if _token_overlap(candidate_tokens, existing_tokens) >= 0.58:
            return True
    return False


def _token_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))
