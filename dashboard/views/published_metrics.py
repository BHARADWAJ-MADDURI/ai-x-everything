import streamlit as st

from dashboard.view_models import metrics_empty_state


def render(data) -> None:
    st.header("Published")
    st.info(metrics_empty_state())
    st.caption("Once Everything × AI starts publishing, this area will track performance and editorial learning.")
