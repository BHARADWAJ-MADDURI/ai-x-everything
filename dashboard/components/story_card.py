import streamlit as st

from src.editorial.models import RecommendedPost


def render_recommendation_card(post: RecommendedPost, title: str) -> None:
    angle = post.selected_angle
    st.markdown(f"### {title}")
    cols = st.columns(4)
    cols[0].metric("Priority", f"{post.priority:.3f}")
    cols[1].metric("Urgency", post.urgency.value.upper())
    cols[2].metric("Angle", angle.angle_type.value.upper())
    cols[3].metric("Status", post.status.value.upper())
    st.caption(f"Audience: {', '.join(audience.value for audience in post.audience)}")
    if post.recommended_publish_window:
        st.caption(f"Publish by: {post.recommended_publish_window}")
    with st.expander("Why this is recommended", expanded=False):
        for reason in post.rationale:
            st.write(f"- {reason}")
