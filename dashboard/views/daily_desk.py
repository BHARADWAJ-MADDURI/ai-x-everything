import streamlit as st

from dashboard.content_packages import generate_session_package, has_approve_decision, package_summary
from dashboard.components.story_card import render_recommendation_card
from dashboard.state import record_decision_in_session
from dashboard.view_models import dashboard_counts
from src.editorial.models import HumanDecisionAction


def render(data) -> None:
    st.header("Daily Desk")
    counts = dashboard_counts(data)
    cols = st.columns(4)
    cols[0].metric("Discovered", counts["discovered"])
    cols[1].metric("Verified", counts["verified"])
    cols[2].metric("Recommended", counts["recommended"])
    cols[3].metric("Review", counts["requiring_review"])

    st.subheader("Today's Recommendations")
    if not data.plan.recommended_posts:
        st.info("No recommendations for today.")
        return
    titles = {story.story_id: story.story.canonical_title for story in data.stories}
    for index, post in enumerate(data.plan.recommended_posts, start=1):
        with st.container(border=True):
            st.caption(f"POST {index}")
            render_recommendation_card(post, titles.get(post.story_id, post.story_id or "Bundle"))
            cols = st.columns(5)
            if cols[0].button("Review", key=f"review-{index}"):
                st.session_state["selected_story_id"] = post.story_id
            if cols[1].button("Approve", key=f"approve-{index}"):
                record_decision_in_session(st, action=HumanDecisionAction.APPROVE, target_id=post.story_id or "unknown")
            if cols[2].button("Save", key=f"save-{index}"):
                record_decision_in_session(st, action=HumanDecisionAction.SAVE, target_id=post.story_id or "unknown")
            if cols[3].button("Hold", key=f"hold-{index}"):
                record_decision_in_session(st, action=HumanDecisionAction.HOLD, target_id=post.story_id or "unknown")
            if cols[4].button("Reject", key=f"reject-{index}"):
                st.session_state["pending_confirmation"] = ("reject", post.story_id or "unknown")
            approved = has_approve_decision(st.session_state["decision_log"], post.story_id or "")
            if approved:
                if st.button("Generate Content Package", key=f"generate-package-{index}"):
                    package = generate_session_package(data, post)
                    st.session_state["content_packages"][post.story_id] = package
            else:
                st.caption("Approve this story to enable content package generation.")
            package = st.session_state["content_packages"].get(post.story_id)
            if package:
                with st.expander("Content package preview", expanded=False):
                    for line in package_summary(package):
                        st.write(line)
