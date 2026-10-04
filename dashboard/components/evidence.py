import streamlit as st

from dashboard.view_models import ProvenanceRow


def render_provenance(rows: list[ProvenanceRow]) -> None:
    if not rows:
        st.info("No verified claim provenance available.")
        return
    for row in rows:
        with st.expander(f"{row.claim_kind.value.upper()} — {row.claim_text}", expanded=False):
            st.markdown("**Evidence**")
            st.write(row.evidence_text)
            st.markdown("**Source**")
            st.write(row.source_name)
            st.caption(f"{row.source_type} | {row.source_url}")
