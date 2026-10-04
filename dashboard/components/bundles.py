import streamlit as st

from dashboard.view_models import bundle_story_sections
from src.editorial.models import BundleCandidate, StoryPlanningInput


def render_bundle(bundle: BundleCandidate, stories: list[StoryPlanningInput]) -> None:
    st.markdown(f"### {bundle.proposed_thesis}")
    cols = st.columns(2)
    cols[0].metric("Fit", "Strong" if bundle.coherence_score >= 0.8 else "Moderate")
    cols[1].metric("Editorial value", "High" if bundle.editorial_value >= 0.8 else "Moderate")
    st.write(bundle.rationale)
    st.caption("Stories remain independently sourced.")
    sections = bundle_story_sections(bundle, stories)
    for story_id, claim_ids in sections.items():
        with st.expander(f"Evidence behind {story_id}", expanded=False):
            st.write(f"{len(claim_ids)} verified supporting claim{'s' if len(claim_ids) != 1 else ''}.")
            with st.expander("Technical Details", expanded=False):
                st.write(", ".join(claim_ids) or "No claim refs.")
