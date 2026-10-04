import streamlit as st

from dashboard.view_models import evergreen_library_items, saved_library_items


def render(data) -> None:
    st.header("Library")

    st.subheader("Saved for Later")
    saved = saved_library_items(data, st.session_state["decision_log"])
    if not saved:
        st.info("No saved items yet.")
    for item in saved:
        with st.container(border=True):
            st.markdown(f"### {item.title}")
            st.write(item.helper)
            st.caption(item.status)

    st.subheader("Evergreen")
    evergreen = evergreen_library_items(data)
    if not evergreen:
        st.info("No evergreen items available.")
    for item in evergreen:
        with st.container(border=True):
            st.markdown(f"### {item.title}")
            st.write(item.helper)
            st.caption(item.status)

    st.subheader("Follow-up Opportunities")
    st.info("Follow-up candidates will appear here once publication history is available.")
