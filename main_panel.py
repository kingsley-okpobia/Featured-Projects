"""
main_panel.py
Renders the main panel: title, metric cards, entity pills,
column tags, data preview, and results tabs.
"""
import pandas as pd
import streamlit as st


def render_header() -> None:
    st.markdown('<div class="pg-title">PrivacyGuard UI</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-subtitle">Local PII redaction at a glance.</div>',
        unsafe_allow_html=True,
    )


def render_metric_cards() -> None:
    sc = (
        f"{st.session_state.privacy_score}/100"
        if st.session_state.privacy_score is not None
        else "—"
    )
    fp = st.session_state.files_processed
    ed = (
        sum(st.session_state.entity_counts.values())
        if st.session_state.entity_counts
        else "—"
    )

    st.markdown(f"""
<div class="pg-cards">
  <div class="pg-card">
    <div class="pg-card-label">Privacy Score</div>
    <div class="pg-card-value">{sc}</div>
    <div class="pg-card-icon pg-icon-t">🛡️</div>
  </div>
  <div class="pg-card">
    <div class="pg-card-label">Files Processed</div>
    <div class="pg-card-value">{fp}</div>
    <div class="pg-card-icon pg-icon-b">📄</div>
  </div>
  <div class="pg-card">
    <div class="pg-card-label">Entities Detected</div>
    <div class="pg-card-value">{ed}</div>
    <div class="pg-card-icon pg-icon-c">🔍</div>
  </div>
</div>""", unsafe_allow_html=True)


def render_entity_pills() -> None:
    if st.session_state.entity_counts:
        pills = " · ".join(
            f"<b>{k}</b> {v}"
            for k, v in st.session_state.entity_counts.items()
        )
        st.markdown(
            f'<div class="pg-pills">{pills}</div>',
            unsafe_allow_html=True,
        )


def render_file_caption() -> None:
    st.markdown(
        f'<div style="font-size:12px;color:#bbb;margin:14px 0 0">'
        f'{st.session_state.file_type} · {st.session_state.file_name} · '
        f'{len(st.session_state.df):,} rows · '
        f'{len(st.session_state.df.columns)} columns</div>',
        unsafe_allow_html=True,
    )


def render_column_tags(sel_cols: list[str]) -> None:
    st.markdown('<div class="pg-sec">Columns to scan</div>',
                unsafe_allow_html=True)
    if sel_cols:
        tags = "".join(
            f'<span class="pg-tag">{c} ✕</span>' for c in sel_cols
        )
        st.markdown(
            f'<div style="margin:4px 0 10px">{tags}</div>',
            unsafe_allow_html=True,
        )


def render_data_preview(df: pd.DataFrame) -> None:
    st.markdown('<div class="pg-sec">Data preview</div>',
                unsafe_allow_html=True)
    st.dataframe(df.head(100), use_container_width=True, height=260)


def render_results(df: pd.DataFrame, sel_cols: list[str]) -> None:
    rdf = st.session_state.results_df
    st.markdown('<div class="pg-sec">Results</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Cleaned data", "Diff view"])

    with tab1:
        st.dataframe(rdf, use_container_width=True, height=380)

    with tab2:
        rows = []
        for i in range(min(200, len(df))):
            row = {"Row": i}
            for col in sel_cols:
                row[f"{col} — original"] = str(df.at[i, col])
                row[f"{col} — redacted"]  = str(rdf.at[i, col])
            rows.append(row)
        st.dataframe(
            pd.DataFrame(rows), use_container_width=True, height=380
        )