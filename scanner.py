"""
scanner.py — two-pass architecture
Pass 1: Vectorised regex (milliseconds, no model)
Pass 2: NER model on remaining text only (batched, fast model)
"""
import streamlit as st
import pandas as pd
from opentelemetry import trace

from redaction import (
    force_redact_cell, column_force_type,
    TAGS, _synthetic_replacement,
    regex_redact_series, FAST_PATTERNS,
    redact_cell,
)

tracer = trace.get_tracer(__name__)

# Columns where regex alone is sufficient — skip model entirely
REGEX_ONLY_COLS = {"email", "phone", "ip address", "ip_address",
                   "ipaddress", "date", "dob", "postcode", "zip"}


def run_scan(df, sel_cols, mode, allowlist, threshold, ner):
    results_df    = df.copy()
    for col in sel_cols:
        results_df[col] = results_df[col].astype(object)

    audit_rows:    list[dict] = []
    entity_counts: dict[str, int] = {}
    changed_cells = 0
    total_cols    = len(sel_cols)

    prog = st.progress(0, text="Starting scan…")

    for ci, col in enumerate(sel_cols):
        col_lower  = col.lower().strip()
        force_type = column_force_type(col)

        with tracer.start_as_current_span(f"scan_column.{col}") as col_span:
            col_span.set_attribute("column.name", col)
            col_span.set_attribute("column.rows", len(df))

            prog.progress((ci / total_cols),
                          text=f"Pass 1 — regex: {col}")

            # ── Force-redact columns (address, IP by name) ─────────────
            if force_type:
                for ri, val in enumerate(df[col]):
                    sv = str(val)
                    if sv.strip() in ("nan", "None", ""):
                        continue
                    rep, etype = force_redact_cell(sv, mode, force_type)
                    results_df.at[ri, col] = rep
                    audit_rows.append({
                        "column": col, "row": ri,
                        "original_preview": sv[:3] + "***",
                        "entity_type": etype,
                        "replacement": rep,
                        "confidence":  1.0,
                        "action": "Synthesized" if mode == "Synthetic"
                                  else "Redacted",
                    })
                    changed_cells += 1
                    entity_counts[etype] = entity_counts.get(etype, 0) + 1

            else:
                # ── Pass 1: Vectorised regex ───────────────────────────
                cleaned_series, regex_findings = regex_redact_series(
                    df[col], mode, allowlist
                )
                results_df[col] = cleaned_series

                for f in regex_findings:
                    ri = f["row"]
                    et = f["entity_type"]
                    entity_counts[et] = entity_counts.get(et, 0) + 1
                    changed_cells += 1
                    audit_rows.append({
                        "column": col, "row": ri,
                        "original_preview": f["original_preview"],
                        "entity_type":      et,
                        "replacement":      f["replacement"],
                        "confidence":       f["confidence"],
                        "action": "Synthesized" if mode == "Synthetic"
                                  else "Redacted",
                    })

                # ── Pass 2: NER model — only if column needs it ────────
                if col_lower not in REGEX_ONLY_COLS:
                    prog.progress(
                        (ci + 0.5) / total_cols,
                        text=f"Pass 2 — NER model: {col}",
                    )

                    # Batch all rows at once
                    indices = [
                        ri for ri, val in enumerate(results_df[col])
                        if str(val).strip() not in ("nan", "None", "")
                        and not any(
                            tag in str(val)
                            for tag in TAGS.values()
                        )
                    ]
                    values = [str(results_df.at[ri, col]) for ri in indices]

                    if values:
                        batch_results = ner(values, batch_size=64)

                        for ri, sv, entities in zip(
                            indices, values, batch_results
                        ):
                            if not entities:
                                continue
                            result = sv
                            for ent in sorted(
                                entities,
                                key=lambda x: x["start"],
                                reverse=True,
                            ):
                                if ent["score"] < threshold:
                                    continue
                                text_span = sv[ent["start"]:ent["end"]]
                                etype     = ent.get(
                                    "entity_group",
                                    ent.get("entity", "MISC")
                                )
                                rep = (
                                    TAGS.get(etype, f"[{etype}]")
                                    if mode == "Redaction"
                                    else _synthetic_replacement(etype)
                                )
                                result = (
                                    result[:ent["start"]]
                                    + rep
                                    + result[ent["end"]:]
                                )
                                changed_cells += 1
                                entity_counts[etype] = (
                                    entity_counts.get(etype, 0) + 1
                                )
                                audit_rows.append({
                                    "column": col, "row": ri,
                                    "original_preview": sv[:3] + "***",
                                    "entity_type":      etype,
                                    "replacement":      rep,
                                    "confidence":       round(
                                        ent["score"], 3),
                                    "action": (
                                        "Synthesized"
                                        if mode == "Synthetic"
                                        else "Redacted"
                                    ),
                                })
                            results_df.at[ri, col] = result

            col_span.set_attribute(
                "entities.found",
                sum(1 for a in audit_rows if a["column"] == col),
            )

        prog.progress((ci + 1) / total_cols,
                      text=f"Done: {col}")

    prog.empty()

    total_cells = max(len(df) * len(sel_cols), 1)
    st.session_state.privacy_score    = round(
        100 * (1 - changed_cells / total_cells)
    )
    st.session_state.entity_counts    = entity_counts
    st.session_state.results_df       = results_df
    st.session_state.audit_rows       = audit_rows
    st.session_state.scan_done        = True
    st.session_state.files_processed += 1