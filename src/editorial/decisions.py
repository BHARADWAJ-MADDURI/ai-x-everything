from datetime import datetime

from src.editorial.models import HumanDecisionAction, HumanEditorialDecision


def record_human_decision(
    *,
    action: HumanDecisionAction,
    target_id: str,
    decided_at: datetime,
    editor: str | None = None,
    comment: str | None = None,
) -> HumanEditorialDecision:
    return HumanEditorialDecision(
        action=action,
        target_id=target_id,
        decided_at=decided_at,
        editor=editor,
        comment=comment,
    )
