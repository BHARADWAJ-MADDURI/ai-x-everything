import streamlit as st

from dashboard.view_models import metrics_empty_state


def render(data) -> None:
    st.header("Published & Metrics")
    st.info(metrics_empty_state())
    st.caption("Future fields: published date, platform, angle, views, watch time, completion, likes, comments, shares, saves, follows.")
