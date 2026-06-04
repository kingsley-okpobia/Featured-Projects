"""
state.py
Centralised session-state initialisation for the app.
"""
import streamlit as st


DEFAULTS: dict = {
    "files_processed": 0,
    "scan_done":       False,
    "results_df":      None,
    "audit_rows":      [],
    "entity_counts":   {},
    "privacy_score":   None,
    "df":              None,
    "file_type":       None,
    "file_name":       None,
    "col_checks":      {},
}


def init_state() -> None:
    """Initialise all session state keys to their defaults if not set."""
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def reset_scan_state() -> None:
    """Clear scan results when a new file is loaded."""
    st.session_state.col_checks    = {}
    st.session_state.scan_done     = False
    st.session_state.results_df    = None
    st.session_state.entity_counts = {}
    st.session_state.privacy_score = None
    st.session_state.audit_rows    = []