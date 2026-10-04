import streamlit as st


def render(data) -> None:
    st.header("Discovery")
    query = st.text_input("Search title/text")
    urgency = st.multiselect("Urgency", sorted({story.timing.urgency.value for story in data.stories}))
    source_types = st.multiselect(
        "Source type",
        sorted({source.source_type.value for story in data.stories for source in story.story.evidence_pack.sources}),
    )
    for story in data.stories:
        if query and query.lower() not in story.story.canonical_title.lower():
            continue
        if urgency and story.timing.urgency.value not in urgency:
            continue
        if source_types and not any(source.source_type.value in source_types for source in story.story.evidence_pack.sources):
            continue
        with st.container(border=True):
            st.markdown(f"### {story.story.canonical_title}")
            st.caption(f"{story.lifecycle_status.value} | {story.timing.urgency.value} | {story.domain or 'topic unknown'}")
            st.write(story.story.analysis.development_summary)
