import streamlit as st

from dashboard.components.angles import render_angles
from dashboard.components.evidence import render_provenance
from dashboard.view_models import display_timestamp, hashtag_reach_label, provenance_rows


def render(data) -> None:
    st.header("Story Review")
    story_ids = [story.story_id for story in data.stories]
    selected = st.session_state.get("selected_story_id") or (story_ids[0] if story_ids else None)
    if not selected:
        st.info("No verified stories available.")
        return
    selected = st.selectbox("Story", story_ids, index=story_ids.index(selected) if selected in story_ids else 0)
    st.session_state["selected_story_id"] = selected
    story = next(item for item in data.stories if item.story_id == selected)

    st.subheader(story.story.canonical_title)
    st.markdown("#### Editorial")
    cols = st.columns(5)
    cols[0].metric("Editorial score", f"{story.editorial_score:.2f}")
    cols[1].metric("Urgency", story.timing.urgency.value)
    cols[2].metric("Shelf life", story.timing.shelf_life.value)
    cols[3].metric("Publish by", display_timestamp(story.timing.publish_by))
    cols[4].metric("Lifecycle", story.lifecycle_status.value)
    st.caption(story.timing.timing_rationale)

    st.markdown("#### Sources")
    for source in story.story.evidence_pack.sources:
        st.write(f"{source.source_name} | {source.source_type.value} | {source.evidence_role.value}")
        st.caption(source.source_url)

    st.markdown("#### Provenance")
    render_provenance(provenance_rows(story))

    st.markdown("#### Rejected Claims")
    if story.story.rejected_claims:
        for rejected in story.story.rejected_claims:
            st.write(f"{rejected.item_id}: {rejected.reason}")
    else:
        st.info("No rejected claims exposed for this story.")

    st.markdown("#### Angles")
    render_angles(story.story.validated_angles, data.angle_history)

    st.markdown("#### Grounded Titles")
    for title in data.title_candidates_by_story.get(story.story_id, []):
        st.radio(
            title.text,
            [title.text],
            key=f"title-{story.story_id}-{title.text}",
            captions=[f"{title.title_type.value} | clarity {title.clarity:.2f} | hype risk {title.hype_risk:.2f}"],
        )
    manual = st.text_input("Manual title")
    if manual:
        st.warning(f"MANUAL — NOT AUTOMATICALLY VERIFIED: {manual}")

    st.markdown("#### Hashtags")
    for tag in data.hashtag_candidates_by_story.get(story.story_id, []):
        st.checkbox(
            f"{tag.tag} | relevance {tag.relevance_score:.2f} | reach {hashtag_reach_label(tag)}",
            key=f"hashtag-{story.story_id}-{tag.tag}",
        )
