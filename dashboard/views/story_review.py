import streamlit as st

from dashboard.content_packages import (
    approve_session_package_for_render,
    generate_session_package,
)
from dashboard.state import record_decision_in_session
from dashboard.view_models import (
    claim_kind_label,
    content_direction_label,
    editorial_status_label,
    hashtag_choices,
    manual_title_requires_acknowledgement,
    package_preview,
    provenance_display_rows,
    rejected_claim_display_rows,
    title_choices,
    trust_summary,
    validation_summary,
)
from src.editorial.models import HumanDecisionAction


STAGES = ["understand", "choose", "create", "approve"]
STAGE_LABELS = {
    "understand": "1 Understand",
    "choose": "2 Choose",
    "create": "3 Create",
    "approve": "4 Approve",
}


def render(data) -> None:
    story_ids = [story.story_id for story in data.stories]
    selected = st.session_state.get("selected_story_id") or (story_ids[0] if story_ids else None)
    if not selected:
        st.info("No verified stories available.")
        return

    story = next(item for item in data.stories if item.story_id == selected)
    post = next((item for item in data.plan.recommended_posts if item.story_id == selected), None)
    package = st.session_state["content_packages"].get(story.story_id)
    status = editorial_status_label(
        story_id=story.story_id,
        decision_log=st.session_state["decision_log"],
        package=package,
    )

    top_cols = st.columns([1, 5])
    if top_cols[0].button("Back to Today"):
        st.session_state["selected_story_id"] = None
        st.session_state["workflow_stage"] = "understand"
        st.rerun()
    top_cols[1].caption(f"Status: {status}")

    st.header(story.story.canonical_title)
    stage = st.session_state.get("workflow_stage", "understand")
    if stage not in STAGES:
        stage = "understand"
    selected_label = st.radio(
        "Workflow",
        [STAGE_LABELS[item] for item in STAGES],
        index=STAGES.index(stage),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["workflow_stage"] = next(
        key for key, label in STAGE_LABELS.items() if label == selected_label
    )

    if st.session_state["workflow_stage"] == "understand":
        _render_understand(story, post)
    elif st.session_state["workflow_stage"] == "choose":
        _render_choose(data, story, post)
    elif st.session_state["workflow_stage"] == "create":
        _render_create(data, story, post, package)
    else:
        _render_approve(data, story, package)


def _render_understand(story, post) -> None:
    trust = trust_summary(story)
    timing = "Publish today" if story.timing.urgency.value == "breaking" else "Can wait"
    st.subheader("What happened")
    st.write(story.story.analysis.development_summary)
    st.subheader("Why it matters")
    st.write(post.selected_angle.thesis if post else story.story.analysis.development_summary)
    cols = st.columns(3)
    cols[0].metric("Timing", f"{story.timing.urgency.value.title()} / {timing}")
    cols[1].metric("Trust", "Verified")
    cols[2].metric("Sources", trust.source_count)
    st.caption(trust.label)

    with st.expander("View Sources & Evidence", expanded=False):
        for row in provenance_display_rows(story):
            st.markdown(f"**{row.label}**")
            st.write(row.text)
            st.markdown("Evidence")
            st.write(row.evidence)
            st.caption(f"{row.source_name} · {row.source_url}")
        rejected = rejected_claim_display_rows(story)
        if rejected:
            st.markdown("#### Not established")
            for row in rejected:
                st.markdown(f"**{row.label}**")
                st.write(row.text)
                if row.evidence:
                    st.caption(row.evidence)
        with st.expander("Technical Details", expanded=False):
            st.write("Claim, evidence, and source IDs are retained internally for auditability.")

    if st.button("Choose Direction"):
        st.session_state["workflow_stage"] = "choose"
        st.rerun()


def _render_choose(data, story, post) -> None:
    st.subheader("Recommended direction")
    if post:
        st.markdown(f"**{content_direction_label(post.selected_angle)}**")
        st.write(post.selected_angle.thesis)
        st.caption(
            "Audience: "
            + ", ".join(audience.value for audience in post.selected_angle.target_audiences)
        )
        st.info("This direction creates a grounded content draft for short-form video and platform adaptations.")

    st.markdown("#### Alternative angles")
    selected_angle_id = st.session_state.get("selected_angle_id") or (post.selected_angle.id if post else None)
    for angle in story.story.validated_angles:
        disabled = angle.rejected or angle.angle_type in data.angle_history.rejected_angle_types
        label = content_direction_label(angle)
        selected = angle.id == selected_angle_id
        with st.container(border=True):
            st.markdown(f"**{'Selected: ' if selected else ''}{label}**")
            st.write(angle.thesis)
            st.caption("Unavailable" if disabled else "Available")
            if st.button(
                "Selected" if selected else "Select angle",
                key=f"select-angle-{story.story_id}-{angle.id}",
                disabled=disabled or selected,
            ):
                st.session_state["selected_angle_id"] = angle.id
                st.rerun()

    st.markdown("#### Title")
    titles = data.title_candidates_by_story.get(story.story_id, [])
    choices = title_choices(titles, st.session_state.get("selected_title"))
    title_texts = [choice.text for choice in choices]
    if title_texts:
        current = next((choice.text for choice in choices if choice.selected), title_texts[0])
        selected_title = st.radio(
            "Title choice",
            title_texts,
            index=title_texts.index(current),
            captions=[choice.helper for choice in choices],
        )
        st.session_state["selected_title"] = selected_title
        st.success("Selected title is grounded.")
    manual = st.text_input("Manual title")
    if manual:
        st.warning(f"MANUAL - NOT AUTOMATICALLY VERIFIED: {manual}")
        st.session_state["selected_title"] = manual

    st.markdown("#### Hashtags")
    tags = data.hashtag_candidates_by_story.get(story.story_id, [])
    existing_tags = st.session_state.get("selected_hashtags") or {tag.tag for tag in tags}
    selected_tags = set()
    for choice in hashtag_choices(tags, existing_tags):
        checked = st.checkbox(
            choice.tag,
            value=choice.selected,
            key=f"hashtag-choice-{story.story_id}-{choice.tag}",
            help=choice.helper,
        )
        if checked:
            selected_tags.add(choice.tag)
    st.session_state["selected_hashtags"] = selected_tags

    st.divider()
    cols = st.columns([2, 1, 1, 1])
    if cols[0].button("Approve Story & Create Draft"):
        if post:
            record_decision_in_session(st, action=HumanDecisionAction.APPROVE, target_id=story.story_id)
            package = generate_session_package(
                data,
                post,
                selected_title_text=st.session_state.get("selected_title"),
                selected_hashtag_tags=st.session_state.get("selected_hashtags"),
            )
            st.session_state["content_packages"][story.story_id] = package
            st.session_state["workflow_stage"] = "create"
            st.success("Story approved and draft generated.")
            st.rerun()
    if cols[1].button("Save"):
        record_decision_in_session(st, action=HumanDecisionAction.SAVE, target_id=story.story_id)
        st.success("Saved for later.")
    if cols[2].button("Hold"):
        record_decision_in_session(st, action=HumanDecisionAction.HOLD, target_id=story.story_id)
        st.success("Held.")
    if cols[3].button("Reject"):
        st.session_state["pending_confirmation"] = ("reject", story.story_id)
        st.rerun()


def _render_create(data, story, post, package) -> None:
    st.subheader("Content Draft")
    if package is None:
        if post and st.button("Create Draft"):
            package = generate_session_package(
                data,
                post,
                selected_title_text=st.session_state.get("selected_title"),
                selected_hashtag_tags=st.session_state.get("selected_hashtags"),
            )
            st.session_state["content_packages"][story.story_id] = package
            st.success("Draft generated.")
            st.rerun()
        else:
            st.info("Approve the story to create a grounded draft.")
        return

    preview = package_preview(package)
    tabs = st.tabs(["Reel", "Instagram", "Blog", "LinkedIn", "X", "TikTok", "YouTube"])
    with tabs[0]:
        st.markdown("#### Hook")
        st.write(preview.reel_hook)
        st.markdown("#### Narration")
        st.write(preview.reel_narration)
        st.caption(f"Target duration: {preview.reel_target_duration} seconds")
        st.markdown("#### Scenes")
        for index, scene in enumerate(preview.reel_scenes, start=1):
            with st.container(border=True):
                st.markdown(f"**Scene {index}: {scene.purpose}**")
                st.write(scene.narration)
                st.caption(f"On-screen: {scene.on_screen_text}")
                st.caption(f"Visual direction: {scene.visual_direction} · {scene.duration_hint}")
        st.markdown("#### CTA")
        st.write(preview.reel_cta)
    with tabs[1]:
        st.write(preview.instagram_caption)
        st.caption(" ".join(preview.instagram_hashtags))
    with tabs[2]:
        st.markdown(f"### {preview.blog_headline}")
        st.caption(preview.blog_dek)
        st.write(preview.blog_body)
    with tabs[3]:
        st.write(preview.linkedin_post)
    with tabs[4]:
        for item in preview.x_posts:
            st.write(item)
    with tabs[5]:
        st.write(preview.tiktok_caption)
        st.caption(" ".join(preview.tiktok_hashtags))
    with tabs[6]:
        st.markdown(f"### {preview.youtube_title}")
        st.write(preview.youtube_description)

    _render_validation(package)
    if st.button("Continue to Approval"):
        st.session_state["workflow_stage"] = "approve"
        st.rerun()


def _render_approve(data, story, package) -> None:
    st.subheader("Content Review")
    if package is None:
        st.info("No draft generated yet.")
        return
    validation = validation_summary(package)
    st.write("Story approved: yes")
    st.write("Draft generated: yes")
    st.write(f"Grounding checks: {'ready' if validation.ready else 'needs review'}")
    st.write(f"Ready for render: {'yes' if package.review_state.value == 'approved_for_render' else 'not yet'}")
    _render_validation(package)

    if manual_title_requires_acknowledgement(package):
        st.warning("Manual title requires acknowledgement before render approval.")
        acknowledged = st.checkbox("I acknowledge this manual title was not automatically verified.")
        if not acknowledged:
            return

    if package.review_state.value == "approved_for_render":
        st.success("READY FOR RENDER")
        if st.button("Return to Today"):
            st.session_state["selected_story_id"] = None
            st.session_state["workflow_stage"] = "understand"
            st.rerun()
        return

    if st.button("Approve for Render"):
        approved = approve_session_package_for_render(data, package)
        st.session_state["content_packages"][story.story_id] = approved
        if approved.review_state.value == "approved_for_render":
            st.success("READY FOR RENDER")
        else:
            st.warning("Draft needs review before render.")
        st.rerun()


def _render_validation(package) -> None:
    summary = validation_summary(package)
    st.markdown("#### Content Check")
    for line in summary.lines:
        st.write(f"{'OK' if summary.ready else 'Review'} - {line}")
    with st.expander("View Validation Details", expanded=False):
        st.write(
            "Deterministic validation checks claim references, source references, numeric material, "
            "platform readiness, and manual-title acknowledgement. It does not semantically prove every sentence."
        )
        if package.validation and package.validation.issues:
            for issue in package.validation.issues:
                st.write(issue)
        else:
            st.write("No validation issues reported.")
