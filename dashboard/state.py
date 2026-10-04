from datetime import datetime, timezone

from dashboard.view_models import AuditEntry, audit_entry, create_decision
from src.editorial.models import HumanDecisionAction


def ensure_dashboard_state(st) -> None:
    st.session_state.setdefault("decision_log", [])
    st.session_state.setdefault("selected_story_id", None)
    st.session_state.setdefault("selected_angle_id", None)
    st.session_state.setdefault("selected_title", None)
    st.session_state.setdefault("selected_hashtags", set())
    st.session_state.setdefault("pending_confirmation", None)
    st.session_state.setdefault("content_packages", {})


def record_decision_in_session(
    st,
    *,
    action: HumanDecisionAction,
    target_id: str,
    comment: str | None = None,
    confirmed: bool = False,
) -> AuditEntry:
    decision = create_decision(
        action=action,
        target_id=target_id,
        decided_at=datetime.now(timezone.utc),
        comment=comment,
        confirmed=confirmed,
    )
    entry = audit_entry(decision)
    st.session_state["decision_log"].append(entry)
    return entry
