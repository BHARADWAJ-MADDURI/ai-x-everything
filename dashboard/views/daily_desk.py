import streamlit as st

from dashboard.components.bundles import render_bundle
from dashboard.content_packages import generate_session_package
from dashboard.state import record_decision_in_session
from dashboard.view_models import (
    StoryCardViewModel,
    story_card_view_model,
    today_summary,
)
from src.editorial.models import HumanDecisionAction, RecommendedPost, StoryPlanningInput


def render(data) -> None:
    st.header("Today")
    summary = today_summary(
        data,
        st.session_state["decision_log"],
        st.session_state["content_packages"],
    )
    st.markdown(
        f"**{summary['attention']} stories worth your attention**  \n"
        f"{summary['needs_decision']} need a decision · "
        f"{summary['draft_ready']} drafts generated · "
        f"{summary['ready_for_render']} ready for render"
    )

    if not data.plan.recommended_posts:
        st.info("No recommendations for today.")
        return

    stories = {story.story_id: story for story in data.stories}
    first, rest = data.plan.recommended_posts[0], data.plan.recommended_posts[1:]
    first_story = stories.get(first.story_id)
    if first_story:
        st.divider()
        st.subheader("Work on this first")
        _render_story_card(first, first_story, featured=True, key_prefix="first")

    ready_posts = [
        post
        for post in data.plan.recommended_posts
        if post.story_id in st.session_state["content_packages"] and post.story_id != first.story_id
    ]
    if ready_posts:
        st.divider()
        st.subheader("Ready")
        for post in ready_posts:
            story = stories.get(post.story_id)
            if story:
                _render_story_card(post, story, key_prefix=f"ready-{post.story_id}")

    if rest:
        st.divider()
        st.subheader("Next")
        for post in rest:
            story = stories.get(post.story_id)
            if story:
                _render_story_card(post, story, key_prefix=f"next-{post.story_id}")

    st.divider()
    st.subheader("Bundle Opportunities")
    if not data.plan.bundle_candidates:
        st.info("No bundle opportunities.")
    for bundle in data.plan.bundle_candidates:
        with st.container(border=True):
            render_bundle(bundle, data.stories)
            cols = st.columns([1, 1, 4])
            if cols[0].button("Approve bundle", key=f"approve-bundle-{bundle.bundle_id}"):
                st.session_state["pending_confirmation"] = ("approve_bundle", bundle.bundle_id)
            if cols[1].button("Keep separate", key=f"keep-separate-{bundle.bundle_id}"):
                record_decision_in_session(
                    st,
                    action=HumanDecisionAction.KEEP_SEPARATE,
                    target_id=bundle.bundle_id,
                )
                st.success("Bundle kept separate.")


def _render_story_card(
    post: RecommendedPost,
    story: StoryPlanningInput,
    *,
    featured: bool = False,
    key_prefix: str,
) -> None:
    package = st.session_state["content_packages"].get(story.story_id)
    card = story_card_view_model(
        post=post,
        story=story,
        decision_log=st.session_state["decision_log"],
        package=package,
    )
    with st.container(border=True):
        if featured:
            st.caption(card.priority_label)
        _render_card_body(card)
        primary_col, save_col, hold_col, reject_col = st.columns([2, 1, 1, 1])
        if primary_col.button(card.primary_action, key=f"{key_prefix}-primary-{story.story_id}-{card.status_label}"):
            _handle_primary_action(post, card)
        if save_col.button("Save", key=f"{key_prefix}-save-{story.story_id}"):
            record_decision_in_session(st, action=HumanDecisionAction.SAVE, target_id=story.story_id)
            st.success("Saved for later.")
            st.rerun()
        if hold_col.button("Hold", key=f"{key_prefix}-hold-{story.story_id}"):
            record_decision_in_session(st, action=HumanDecisionAction.HOLD, target_id=story.story_id)
            st.success("Held.")
            st.rerun()
        if reject_col.button("Reject", key=f"{key_prefix}-reject-{story.story_id}"):
            st.session_state["pending_confirmation"] = ("reject", story.story_id)
            st.rerun()


def _render_card_body(card: StoryCardViewModel) -> None:
    st.markdown(f"### {card.headline}")
    st.markdown(f"**What happened:** {card.what_happened}")
    st.markdown(f"**Why it matters:** {card.why_it_matters}")
    st.caption(
        f"{card.urgency_label} · {card.timing_label} · {card.trust_label} · "
        f"Recommended: {card.content_direction}"
    )
    st.markdown(f"**Status:** {card.status_label}")


def _handle_primary_action(post: RecommendedPost, card: StoryCardViewModel) -> None:
    if card.status_label == "APPROVED":
        package = generate_session_package(
            st.session_state["dashboard_data"],
            post,
            selected_title_text=st.session_state.get("selected_title"),
            selected_hashtag_tags=st.session_state.get("selected_hashtags"),
        )
        st.session_state["content_packages"][card.story_id] = package
        st.session_state["selected_story_id"] = card.story_id
        st.session_state["workflow_stage"] = "create"
        st.success("Draft generated.")
        st.rerun()
    else:
        st.session_state["selected_story_id"] = card.story_id
        st.session_state["workflow_stage"] = "understand"
        st.rerun()
