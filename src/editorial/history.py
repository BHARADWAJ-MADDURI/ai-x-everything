from src.editorial.models import AngleHistory, FollowUpPotential
from src.intelligence.models import AngleType, PotentialAngle


def published_angle_types(story_id: str, history: AngleHistory) -> set[AngleType]:
    return {
        record.angle_type
        for record in history.publication_records
        if record.story_id == story_id
    }


def available_angles(
    story_id: str,
    angles: list[PotentialAngle],
    history: AngleHistory,
) -> list[PotentialAngle]:
    published = published_angle_types(story_id, history)
    return [
        angle
        for angle in angles
        if angle.angle_type not in published
        and angle.angle_type not in history.rejected_angle_types
        and angle.id not in history.rejected_angle_ids
        and not angle.rejected
    ]


def rejected_angles(
    angles: list[PotentialAngle],
    history: AngleHistory,
) -> list[PotentialAngle]:
    return [
        angle
        for angle in angles
        if angle.angle_type in history.rejected_angle_types or angle.id in history.rejected_angle_ids or angle.rejected
    ]


def follow_up_potential(
    story_id: str,
    angles: list[PotentialAngle],
    history: AngleHistory,
) -> FollowUpPotential:
    unused_strong = [
        angle
        for angle in available_angles(story_id, angles, history)
        if _angle_score(angle) >= 0.72
    ]
    if len(unused_strong) >= 3:
        return FollowUpPotential.HIGH
    if len(unused_strong) == 2:
        return FollowUpPotential.MEDIUM
    if len(unused_strong) == 1:
        return FollowUpPotential.LOW
    return FollowUpPotential.NONE


def materially_different_angle(
    story_id: str,
    candidate_angle: PotentialAngle,
    history: AngleHistory,
) -> bool:
    return candidate_angle.angle_type not in published_angle_types(story_id, history)


def _angle_score(angle: PotentialAngle) -> float:
    if angle.score is not None:
        return angle.score
    return (
        angle.evidence_strength * 0.35
        + angle.relevance * 0.25
        + angle.usefulness * 0.25
        + angle.novelty * 0.15
        - angle.speculation_risk * 0.2
    )
