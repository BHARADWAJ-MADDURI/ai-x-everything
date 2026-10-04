import streamlit as st

from dashboard.view_models import bundle_story_sections
from src.editorial.models import BundleCandidate, StoryPlanningInput


def render_bundle(bundle: BundleCandidate, stories: list[StoryPlanningInput]) -> None:
    st.markdown(f"### {bundle.proposed_thesis}")
    cols = st.columns(3)
    cols[0].metric("Coherence", f"{bundle.coherence_score:.3f}")
    cols[1].metric("Editorial value", f"{bundle.editorial_value:.3f}")
    cols[2].metric("Relationship", bundle.relationship_type.value)
    st.write(bundle.rationale)
    st.caption("Stories remain independently sourced.")
    sections = bundle_story_sections(bundle, stories)
    for story_id, claim_ids in sections.items():
        with st.expander(f"{story_id} claims", expanded=False):
            st.write(", ".join(claim_ids) or "No claim refs.")
