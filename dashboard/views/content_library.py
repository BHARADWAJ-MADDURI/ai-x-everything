import streamlit as st


def render(data) -> None:
    st.header("Content Library")
    st.subheader("Evergreen Items")
    if not data.evergreen_items:
        st.info("No evergreen items available.")
    for item in data.evergreen_items:
        with st.container(border=True):
            st.markdown(f"### {item.proposed_thesis}")
            st.caption(f"Origin: {item.originating_story_id} | {item.angle_type.value} | {item.status.value}")
            st.write(f"Audience: {', '.join(audience.value for audience in item.audience)}")
            st.write(f"Review: {item.review_at.isoformat() if item.review_at else 'not scheduled'}")

    st.subheader("Saved Items")
    if not data.plan.saved_for_later:
        st.info("No saved items.")
    for post in data.plan.saved_for_later:
        with st.container(border=True):
            st.markdown(f"### {post.story_id}")
            st.caption(f"{post.selected_angle.angle_type.value} | priority {post.priority:.3f}")

    st.subheader("Follow-up Eligible / Unused Strong Angles")
    st.info("Follow-up eligibility is available from angle history; no persistent publication history is loaded in demo mode.")
