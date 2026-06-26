"""
sidebar.py
Renders the full sidebar matching the Lovable AppSidebar.tsx design.
"""
import io
import csv
import streamlit as st

LANGUAGES = [
    "English", "French", "Spanish", "German", "Japanese", "Portuguese",
    "Italian", "Dutch", "Polish", "Russian", "Chinese (Simplified)",
    "Arabic", "Korean", "Turkish", "Swedish", "Hindi",
]


def render_sidebar(df, selected_cols: list[str]) -> dict:
    """
    Renders the full sidebar and returns a dict of all control values:
        uploaded, lang, allowlist, threshold, mode, run_clicked
    """
    with st.sidebar:

        # ── Logo ──────────────────────────────────────────────────────
        st.markdown(
            '<div class="pg-logo">🛡️ PrivacyGuard UI</div>',
            unsafe_allow_html=True,
        )

        # ── Upload ────────────────────────────────────────────────────
        st.markdown('<div class="pg-slabel">Upload</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "u", type=["csv", "json"], label_visibility="collapsed"
        )
        if uploaded:
            ext = "csv" if uploaded.name.endswith(".csv") else "json"
            st.markdown(
                f'<div style="font-size:12px;color:#647a76;margin-top:2px">'
                f'{uploaded.name}'
                f'<span class="pg-badge pg-{ext}">{ext.upper()}</span></div>',
                unsafe_allow_html=True,
            )

        # ── Language ──────────────────────────────────────────────────
        st.markdown('<div class="pg-slabel">Language</div>', unsafe_allow_html=True)
        lang = st.selectbox("l", LANGUAGES, label_visibility="collapsed")
        if lang != "English":
            st.markdown(
                f'<div style="font-size:11px;color:#aaa;margin-top:-4px">'
                f'MoE head: {lang}</div>',
                unsafe_allow_html=True,
            )

        # ── Allowlist ─────────────────────────────────────────────────
        raw   = st.session_state.get("allowlist_raw", "")
        terms = [a.strip() for a in raw.split(",") if a.strip()]
        n     = len(terms)
        allowlist_raw = st.text_input(
            f"Allowlist — {n} term{'s' if n != 1 else ''}",
            key="allowlist_raw",
            placeholder="e.g. ACME Corp, ProductID-7",
        )
        allowlist = [a.strip() for a in allowlist_raw.split(",") if a.strip()]

        # ── Advanced settings ─────────────────────────────────────────
        with st.expander("Advanced settings", expanded=False):
            sensitivity = st.radio(
                "Detection sensitivity",
                options=["Standard", "High", "Maximum"],
                index=1,
                help="Higher sensitivity catches more PII but may flag some non-PII text.",
                horizontal=True,
            )
            sensitivity_map = {
                "Standard": 0.80,   # high precision, may miss edge cases
                "High":     0.60,   # recommended — balanced
                "Maximum":  0.50,   # catches everything, review before export
            }
            threshold = sensitivity_map[sensitivity]

            st.markdown(
                f'<div style="font-size:11px;color:#647a76;margin-top:4px">'
                f'Standard — fewer flags, high certainty<br>'
                f'High — recommended for most datasets<br>'
                f'Maximum — catches all possible PII, including ambiguous cases'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Columns checklist ─────────────────────────────────────────
        st.markdown('<div class="pg-slabel">Columns</div>', unsafe_allow_html=True)
        sel_cols = []
        if df is not None:
            all_cols  = df.columns.tolist()
            auto_pick = {
                c for c in all_cols if any(
                    k in c.lower()
                    for k in ["name", "email", "phone", "address",
                              "comment", "note", "ip"]
                )
            }
            if set(st.session_state.col_checks.keys()) != set(all_cols):
                st.session_state.col_checks = {
                    c: (c in auto_pick) for c in all_cols
                }
            for col in all_cols:
                chk = st.checkbox(
                    col,
                    value=st.session_state.col_checks.get(col, False),
                    key=f"chk_{col}",
                )
                st.session_state.col_checks[col] = chk
                if chk:
                    sel_cols.append(col)
        else:
            st.markdown(
                '<div style="font-size:12px;color:#ccc">'
                'Upload a file to see columns</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Mode ──────────────────────────────────────────────────────
        st.markdown('<div class="pg-slabel">Mode</div>', unsafe_allow_html=True)
        mode = st.radio("m", ["Redaction", "Synthetic"],
                        label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Download buttons ──────────────────────────────────────────
        if st.session_state.scan_done and st.session_state.results_df is not None:
            rdf   = st.session_state.results_df
            fname = (st.session_state.file_name or "output").rsplit(".", 1)[0]
            ftype = st.session_state.file_type or "CSV"

            if ftype == "CSV":
                od, oe, om = (
                    rdf.to_csv(index=False).encode(), "csv", "text/csv"
                )
            else:
                od, oe, om = (
                    rdf.to_json(orient="records", indent=2).encode(),
                    "json", "application/json",
                )

            st.download_button(
                "⬇  Download Cleaned File", od,
                file_name=f"{fname}_privacyguard.{oe}",
                mime=om, use_container_width=True,
            )

            if st.session_state.audit_rows:
                buf = io.StringIO()
                w   = csv.DictWriter(buf, fieldnames=[
                    "column", "row", "original_preview",
                    "entity_type", "replacement", "confidence", "action",
                ])
                w.writeheader()
                w.writerows(st.session_state.audit_rows)
                st.download_button(
                    "📋  Download Audit Report",
                    buf.getvalue().encode(),
                    file_name=f"{fname}_audit.csv",
                    mime="text/csv", use_container_width=True,
                )
        else:
            st.markdown(
                '<div class="pg-dl-placeholder">⬇  Download Cleaned File</div>'
                '<div class="pg-dl-placeholder">📋  Download Audit Report</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Run Scan ──────────────────────────────────────────────────
        run = st.button("▶  Run Scan", use_container_width=True)
        if st.session_state.scan_done:
            st.markdown(
                '<div class="pg-scan-ok">Scan complete</div>',
                unsafe_allow_html=True,
            )

    return {
        "uploaded":  uploaded,
        "lang":      lang,
        "allowlist": allowlist,
        "threshold": threshold if "threshold" in dir() else 0.80,
        "mode":      mode,
        "sel_cols":  sel_cols,
        "run":       run,
    }