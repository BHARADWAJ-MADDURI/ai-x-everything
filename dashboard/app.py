from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from dashboard.components.bundles import render_bundle
from dashboard.components.decisions import render_decision_log
from dashboard.demo_data import load_demo_dashboard_data, load_live_boundary_data
from dashboard.state import ensure_dashboard_state, record_decision_in_session
from dashboard.view_models import dashboard_counts
from dashboard.views import content_library, daily_desk, discovery, published_metrics, story_review
from src.editorial.models import HumanDecisionAction


st.set_page_config(page_title="Everything × AI Editorial Command Center", layout="wide")
ensure_dashboard_state(st)

st.markdown(
    """
    <style>
    :root {
      --exai-ink: #1f2523;
      --exai-muted: #5f6661;
      --exai-bg: #f7f3ed;
      --exai-panel: #fffaf2;
      --exai-border: #d9ccbb;
      --exai-sidebar: #eee7db;
      --exai-accent: #335c67;
    }
    .stApp {
      background: var(--exai-bg);
      color: var(--exai-ink);
    }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stMarkdown, .stCaptionContainer, [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"], [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
      color: var(--exai-ink);
    }
    h1, h2, h3 {
      letter-spacing: 0;
      color: var(--exai-ink);
    }
    .stCaptionContainer, small, [data-testid="stCaptionContainer"] {
      color: var(--exai-muted);
    }
    section[data-testid="stSidebar"] {
      background: var(--exai-sidebar);
      color: var(--exai-ink);
    }
    section[data-testid="stSidebar"] * {
      color: var(--exai-ink);
    }
    div[data-testid="stMetric"],
    div[data-testid="stVerticalBlockBorderWrapper"] {
      background: var(--exai-panel);
      border-color: var(--exai-border);
    }
    div[data-testid="stMetric"] {
      border: 1px solid var(--exai-border);
      padding: 12px;
    }
    .stButton button {
      background: #fdf8ef;
      border: 1px solid var(--exai-border);
      color: var(--exai-ink);
    }
    .stButton button:hover {
      border-color: var(--exai-accent);
      color: var(--exai-ink);
    }
    input, textarea, select {
      color: var(--exai-ink) !important;
      background: #fffdf8 !important;
    }
    a {
      color: var(--exai-accent);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

mode = st.sidebar.radio("Mode", ["Demo", "Live boundary"], horizontal=True)
data = load_demo_dashboard_data() if mode == "Demo" else load_live_boundary_data()

st.title("EVERYTHING × AI")
st.caption("Understand what's changing.")
st.markdown(f"**{data.mode_label}**")

counts = dashboard_counts(data)
header_cols = st.columns(5)
header_cols[0].metric("Plan date", data.plan.plan_date.isoformat())
header_cols[1].metric("Discovered", counts["discovered"])
header_cols[2].metric("Verified", counts["verified"])
header_cols[3].metric("Recommended", counts["recommended"])
header_cols[4].metric("Review", counts["requiring_review"])

with st.expander("System status", expanded=False):
    st.write("Discovery: available")
    st.write("Evidence: available")
    st.write("Verification: available")
    st.write("Planner: available")
    st.write("Rendering: available")
    if mode != "Demo":
        st.warning("Live mode is not fully wired to verified story orchestration yet. This view shows the current boundary without making network calls.")

view = st.sidebar.radio(
    "Primary navigation",
    ["Daily Desk", "Discovery", "Story Review", "Content Library", "Published & Metrics"],
)

pending = st.session_state.get("pending_confirmation")
if pending:
    action, target_id = pending
    st.warning(f"Confirm {action.upper()} for {target_id}")
    cols = st.columns(2)
    if cols[0].button("Confirm"):
        mapped = HumanDecisionAction.REJECT if action == "reject" else HumanDecisionAction.APPROVE_BUNDLE
        record_decision_in_session(st, action=mapped, target_id=target_id, confirmed=True)
        st.session_state["pending_confirmation"] = None
    if cols[1].button("Cancel"):
        st.session_state["pending_confirmation"] = None

if view == "Daily Desk":
    daily_desk.render(data)
    st.subheader("Bundle Review")
    if not data.plan.bundle_candidates:
        st.info("No bundle opportunities.")
    for bundle in data.plan.bundle_candidates:
        with st.container(border=True):
            render_bundle(bundle, data.stories)
            cols = st.columns(2)
            if cols[0].button("Approve bundle", key=f"approve-bundle-{bundle.bundle_id}"):
                st.session_state["pending_confirmation"] = ("approve_bundle", bundle.bundle_id)
            if cols[1].button("Keep separate", key=f"keep-separate-{bundle.bundle_id}"):
                record_decision_in_session(st, action=HumanDecisionAction.KEEP_SEPARATE, target_id=bundle.bundle_id)
elif view == "Discovery":
    discovery.render(data)
elif view == "Story Review":
    story_review.render(data)
elif view == "Content Library":
    content_library.render(data)
else:
    published_metrics.render(data)

st.sidebar.divider()
render_decision_log(st.session_state["decision_log"])
