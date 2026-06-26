"""
app.py  —  PrivacyGuard UI entry point
Run with:  streamlit run app.py
 
Module layout
─────────────
app.py          ← this file — orchestration only
model.py        ← NER model loading (@cache_resource)
redaction.py    ← PII detection, regex sweeps, cell redaction
scanner.py      ← full scan loop over df rows/columns
file_parser.py  ← CSV / JSON ingestion
sidebar.py      ← sidebar UI component
main_panel.py   ← main panel UI components
state.py        ← session state initialisation / reset
styles.py       ← all CSS (colours matched to Lovable design tokens)
"""

import streamlit as st

# ── Page config MUST be first Streamlit call ──────────────────────────
st.set_page_config(
    page_title="PrivacyGuard UI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",   # ← confirm this is set
)

# ── Phoenix tracing (initialise after page config) ────────────────────
try:
    import phoenix as px
    from phoenix.otel import register

    if "phoenix_started" not in st.session_state:
        px.launch_app()
        register(project_name="privacy-guard-eval")
        st.session_state.phoenix_started = True
except Exception:
    pass  # Phoenix tracing disabled — app continues normally



# ── Page config (must be first Streamlit call) ────────────────────────
st.set_page_config(
    page_title="PrivacyGuard UI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",   # ← confirm this is set
)

# ── Local modules ─────────────────────────────────────────────────────
from state      import init_state, reset_scan_state
from file_parser import parse_upload
from model      import load_model
from scanner    import run_scan
from sidebar    import render_sidebar
from main_panel import (
    render_header,
    render_metric_cards,
    render_entity_pills,
    render_file_caption,
    render_column_tags,
    render_data_preview,
    render_results,
)

# ── Inject CSS ────────────────────────────────────────────────────────
st.markdown("""<style>
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
    color: #1a2422 !important;
}
[data-testid="block-container"] {
    padding: 2rem 2.5rem !important;
    max-width: 100% !important;
}
[data-testid="stSidebar"] {
    background: #edf5f3 !important;
    border-right: 1px solid #c8d9d6 !important;
    min-width: 220px !important;
    max-width: 220px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1rem 0.875rem !important;
}
/* Force sidebar open and make collapse button visible */
[data-testid="stSidebar"][aria-expanded="false"] {
    display: block !important;
    visibility: visible !important;
    min-width: 220px !important;
    max-width: 220px !important;
    transform: none !important;
}

/* Sidebar collapse/expand toggle button */
[data-testid="stSidebarCollapseButton"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 14px !important;
    left: 226px !important;
    z-index: 999 !important;
    background: #ffffff !important;
    border: 1px solid #c8d9d6 !important;
    border-radius: 50% !important;
    width: 28px !important;
    height: 28px !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

[data-testid="stSidebarCollapseButton"]:hover {
    background: #edf5f3 !important;
}

/* When sidebar is collapsed, move toggle to left edge */
[data-testid="stSidebar"][aria-expanded="false"] ~ * 
[data-testid="stSidebarCollapseButton"] {
    left: 8px !important;
}            
.pg-logo {
    display: flex; align-items: center; gap: 8px;
    font-size: 16px; font-weight: 700; color: #1a2422;
    padding-bottom: 0.9rem; margin-bottom: 0.5rem;
    border-bottom: 1px solid #c8d9d6;
    font-family: 'Outfit', sans-serif; letter-spacing: -0.02em;
}
.pg-slabel {
    font-size: 11px; font-weight: 500; color: #647a76;
    margin: 0.85rem 0 0.25rem; font-family: 'Outfit', sans-serif;
}
.pg-badge {
    display: inline-block; border-radius: 9999px;
    padding: 1px 7px; font-size: 10px; font-weight: 700;
    margin-left: 5px; vertical-align: middle;
}
.pg-csv  { background: #dbeafe; color: #1d4ed8; }
.pg-json { background: #d1fae5; color: #065f46; }
[data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
[data-testid="stFileUploaderDropzone"] {
    padding: 6px !important;
    min-height: 0 !important;
    border: 1px dashed #c8d9d6 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
}
[data-testid="stFileUploader"] label {
    font-size: 11px !important;
    color: #647a76 !important;
    font-weight: 500 !important;
}
[data-testid="stSelectbox"] > div > div {
    border-radius: 8px !important; font-size: 13px !important;
    border-color: #dfe8e6 !important; background: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stTextInput"] label p {
    font-size: 11px !important; color: #647a76 !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stTextInput"] > div > div > input {
    border-radius: 8px !important; font-size: 12px !important;
    border-color: #dfe8e6 !important; font-family: 'Outfit', sans-serif !important;
}
[data-testid="stExpander"] {
    border: none !important; background: transparent !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary {
    font-size: 12px !important; color: #647a76 !important;
    padding: 0 !important; background: transparent !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stExpander"] summary:hover { color: #1a2422 !important; }
[data-testid="stSlider"] label p { font-size: 11px !important; color: #647a76 !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: #f97316 !important;
}
[data-testid="stCheckbox"] { margin: 0 !important; padding: 1px 0 !important; }
[data-testid="stCheckbox"] label span {
    font-size: 13px !important; color: #1a2422 !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stRadio"] > label { display: none !important; }
[data-testid="stRadio"] label span {
    font-size: 13px !important; color: #1a2422 !important;
    font-family: 'Outfit', sans-serif !important;
}
.pg-dl-placeholder {
    border: 1px solid #dfe8e6; border-radius: 8px;
    padding: 8px 12px; font-size: 13px; color: #bbb;
    margin-bottom: 6px; background: #ffffff;
    font-family: 'Outfit', sans-serif;
}
div.stDownloadButton > button {
    background: #ffffff !important; border: 1px solid #dfe8e6 !important;
    border-radius: 8px !important; color: #1a2422 !important;
    font-size: 13px !important; font-weight: 500 !important;
    width: 100% !important; text-align: left !important;
    font-family: 'Outfit', sans-serif !important; margin-bottom: 4px !important;
}
div.stDownloadButton > button:hover { background: #f5f5f5 !important; }
div.stButton > button {
    background: #f97316 !important; border: none !important;
    border-radius: 8px !important; color: #fff !important;
    font-size: 14px !important; font-weight: 600 !important;
    width: 100% !important; padding: 0.55rem !important;
    font-family: 'Outfit', sans-serif !important; letter-spacing: -0.01em !important;
}
div.stButton > button:hover { background: #ea6a08 !important; }
.pg-scan-ok {
    text-align: center; font-size: 11px; color: #647a76;
    margin-top: 4px; font-family: 'Outfit', sans-serif;
}
.pg-title {
    font-size: 26px; font-weight: 700; color: #1a2422;
    margin: 0 0 3px; font-family: 'Outfit', sans-serif; letter-spacing: -0.02em;
}
.pg-subtitle { font-size: 13px; color: #647a76; margin: 0 0 1.4rem; font-family: 'Outfit', sans-serif; }
.pg-cards { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0; margin-bottom: 0; }
.pg-card {
    background: #ffffff; padding: 1.2rem 1.4rem;
    border-top: 1px solid #dfe8e6; border-bottom: 1px solid #dfe8e6;
    border-right: 1px solid #dfe8e6; position: relative;
}
.pg-card:first-child { border-left: 3px solid #39a88a; border-radius: 10px 0 0 10px; }
.pg-card:nth-child(2) { border-left: 3px solid #3b82f6; }
.pg-card:last-child  { border-left: 3px solid #e05a3a; border-radius: 0 10px 10px 0; }
.pg-card-label { font-size: 12px; color: #647a76; margin-bottom: 8px; font-family: 'Outfit', sans-serif; }
.pg-card-value { font-size: 30px; font-weight: 700; color: #1a2422; line-height: 1; font-family: 'Outfit', sans-serif; letter-spacing: -0.02em; }
.pg-card-icon {
    position: absolute; right: 13px; top: 13px; width: 28px; height: 28px;
    border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px;
}
.pg-icon-t { background: #d1faf0; }
.pg-icon-b { background: #dbeafe; }
.pg-icon-c { background: #fee2d5; }
.pg-pills { font-size: 13px; color: #647a76; margin: 12px 0 0; font-family: 'Outfit', sans-serif; }
.pg-pills b { color: #1a2422; }
.pg-sec {
    font-size: 13px; font-weight: 600; color: #1a2422;
    margin: 1.6rem 0 .5rem; padding-bottom: 5px;
    border-bottom: 1px solid #dfe8e6; font-family: 'Outfit', sans-serif;
}
.pg-tag {
    display: inline-flex; align-items: center; gap: 4px;
    background: #fee2e2; color: #c0392b; border-radius: 9999px;
    padding: 3px 10px; font-size: 12px; font-weight: 500;
    margin: 2px; font-family: 'Outfit', sans-serif;
}
[data-testid="stDataFrame"] { border-radius: 8px !important; border: 1px solid #dfe8e6 !important; overflow: hidden !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { font-size: 13px !important; font-family: 'Outfit', sans-serif !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom: 1px solid #dfe8e6 !important; background: transparent !important; }
[data-testid="stProgressBar"] > div > div { background: #f97316 !important; }
[data-testid="stToolbar"] { display: flex !important; }
#MainMenu, footer, header { visibility: hidden !important; }
</style>""", unsafe_allow_html=True)

# ── Initialise session state ──────────────────────────────────────────
init_state()

# ── Sidebar (always rendered so upload widget persists) ───────────────
df = st.session_state.df
controls = render_sidebar(df, st.session_state.get("sel_cols", []))

uploaded  = controls["uploaded"]
mode      = controls["mode"]
allowlist = controls["allowlist"]
threshold = controls["threshold"]
sel_cols  = controls["sel_cols"]
run       = controls["run"]

# ── File parsing ──────────────────────────────────────────────────────
if uploaded:
    if st.session_state.file_name != uploaded.name:
        try:
            df_new, ftype = parse_upload(uploaded)
            st.session_state.df        = df_new
            st.session_state.file_type = ftype
            st.session_state.file_name = uploaded.name
            reset_scan_state()
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

df = st.session_state.df

# ── Main panel ────────────────────────────────────────────────────────
render_header()
render_metric_cards()
render_entity_pills()

if df is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("Upload a CSV or JSON file using the sidebar to begin.")
    st.stop()

render_file_caption()
render_column_tags(sel_cols)
render_data_preview(df)

# ── Run scan ──────────────────────────────────────────────────────────
if run:
    if not sel_cols:
        st.warning(
            "Tick at least one column in the sidebar before scanning."
        )
        st.stop()

    with st.spinner("Loading model…"):
        ner = load_model()

    run_scan(df, sel_cols, mode, allowlist, threshold, ner)
    st.rerun()

# ── Results (shown after scan) ────────────────────────────────────────
if st.session_state.scan_done and st.session_state.results_df is not None:
    render_results(df, sel_cols)