import streamlit as st


def render_decision_log(entries) -> None:
    st.subheader("Decision Audit Log")
    if not entries:
        st.info("No human decisions recorded in this session.")
        return
    for entry in reversed(entries):
        st.write(entry.label)
        if entry.decision.comment:
            st.caption(entry.decision.comment)
