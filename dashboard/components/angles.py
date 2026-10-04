import streamlit as st

from dashboard.view_models import can_select_angle
from src.editorial.models import AngleHistory
from src.intelligence.models import PotentialAngle


def render_angles(angles: list[PotentialAngle], history: AngleHistory) -> None:
    if not angles:
        st.info("No angles available.")
        return
    for angle in angles:
        selectable = can_select_angle(angle, history.rejected_angle_types)
        label = f"{angle.angle_type.value.upper()} — {angle.thesis}"
        with st.expander(label, expanded=False):
            st.write(f"Score: {angle.score if angle.score is not None else 'unscored'}")
            st.write(f"Evidence strength: {angle.evidence_strength:.2f}")
            st.write(f"Speculation risk: {angle.speculation_risk:.2f}")
            st.write(f"Audience: {', '.join(audience.value for audience in angle.target_audiences)}")
            st.write(f"Supporting claim IDs: {', '.join(angle.supporting_fact_ids) or 'none'}")
            if angle.rationale:
                st.write(angle.rationale)
            st.button("Select angle", key=f"select-angle-{angle.id}", disabled=not selectable)
