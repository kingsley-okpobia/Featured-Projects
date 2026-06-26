"""
redaction.py
PII detection, regex sweeps, and cell-level redaction logic.
"""
import re
import random
import pandas as pd

# ── Entity tag maps ───────────────────────────────────────────────────
TAGS: dict[str, str] = {
    # Standard NER labels
    "PER":        "[NAME]",
    "ORG":        "[ORG]",
    "LOC":        "[ADDRESS]",
    "GPE":        "[ADDRESS]",
    "FAC":        "[ADDRESS]",
    "STREET":     "[ADDRESS]",
    "ADDRESS":    "[ADDRESS]",
    "EMAIL":      "[EMAIL]",
    "IP_ADDRESS": "[IPADDRESS]",
    "PHONE":      "[PHONE]",
    "DATE":       "[DATE]",
    "CREDIT_CARD":"[CREDITCARD]",
    "POSTCODE":   "[POSTCODE]",
    "MISC":       "[ID]",
    # OpenMed model specific labels
    "FIRSTNAME":  "[NAME]",
    "LASTNAME":   "[NAME]",
    "MIDDLENAME": "[NAME]",
    "AGE":        "[AGE]",
    "ID":         "[ID]",
    "EMAIL2":     "[EMAIL]",
    "PHONE2":     "[PHONE]",
    "LOCATION":   "[ADDRESS]",
    "CITY":       "[ADDRESS]",
    "COUNTRY":    "[ADDRESS]",
    "ZIPCODE":    "[POSTCODE]",
}

# ── Synthetic replacement pools ───────────────────────────────────────
SYNTHETIC: dict = {
    "PER": [
        "James Smith", "Maria Garcia", "David Chen",
        "Priya Patel", "Sophie Bernard", "Kenji Tanaka",
        "Aisha Okafor", "Lucas Silva", "Emma Johansson",
    ],
    "ADDRESS": [
        "123 Oak Avenue", "456 River Road", "789 Elm Street",
        "22 Birchwood Close", "5 Maple Drive",
    ],
    "EMAIL":       lambda: f"user_{random.randint(1000, 9999)}@example.com",
    "PHONE":       lambda: f"555-{random.randint(1000, 9999)}",
    "IP_ADDRESS":  lambda: f"192.168.0.{random.randint(1, 254)}",
    "CREDIT_CARD": lambda: f"4111-1111-1111-{random.randint(1000,9999)}",
    "POSTCODE":    lambda: f"{random.randint(10000,99999)}",
    "LOC":         ["123 Main St", "456 Oak Ave", "789 River Rd"],
    "DATE":        ["01/01/2000", "15/06/1990", "22/03/1985"],
}

# ── Column-name force-redact lists ────────────────────────────────────
IP_COL_NAMES:   list[str] = ["ip address", "ip_address", "ipaddress", "ip"]
ADDR_COL_NAMES: list[str] = ["address", "addr", "street", "location"]
NAME_COL_NAMES: list[str] = [
    "name", "full name", "full_name", "firstname", "first_name",
    "lastname", "last_name", "surname", "customer name",
    "customer_name", "employee name", "employee_name",
    "patient name", "patient_name", "contact name", "contact_name",
    "author", "submitted by", "prepared by",
]
# ── Slow regex patterns (address sweep inside NER path) ───────────────
ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+[A-Za-z][A-Za-z\s]{2,40}"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|"
    r"Drive|Dr|Court|Ct|Place|Pl|Way|Terrace|Ter|Close|Crescent|Cres|"
    r"NC|NY|CA|TX|FL|GA|IL|PA|OH|MI|WA|MA|AZ|CO|VA|NJ|TN|IN|MO|MD|[A-Z]{2})?"
    r"(?:\s*,\s*[A-Za-z\s]{2,30})?(?:\s+\d{5}(?:-\d{4})?)?\b",
    re.IGNORECASE,
)

NUMERIC_ID_RE = re.compile(r"\b[\d]{2,5}[-\s][\d]{3,6}[-\s][\d]{3,6}\b")

# ── Fast regex patterns — handle without touching the model ───────────
FAST_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    "PHONE": re.compile(
        r'\b(\+?1[\s.\-]?)?(\(?\d{3}\)?[\s.\-]?)?\d{3}[\s.\-]?\d{4}\b'),
    "IP_ADDRESS": re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'),
    "CREDIT_CARD": re.compile(
        r'\b(?:\d{4}[\s\-]?){3}\d{4}\b'),
    "DATE": re.compile(
        r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b'),
    "POSTCODE": re.compile(
        r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b|\b\d{5}(?:-\d{4})?\b'),
}

NAME_CONTEXT_RE = re.compile(
    r"""
    (?:
        # Prefixed names — "Name: John Smith", "By: Maria"
        (?:name|by|from|to|author|submitted\s+by|prepared\s+by|
           contact|customer|client|patient|employee|officer|
           dr\.?|mr\.?|mrs\.?|ms\.?|prof\.?)
        \s*[:\-]?\s*
    )
    ([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})
    |
    # Capitalised two-word sequences not already tagged
    \b([A-Z][a-z]{1,20}\s+[A-Z][a-z]{1,20})\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Blocklist — common non-name capitalised pairs
NAME_BLOCKLIST = {
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march",
    "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "new york", "los angeles",
    "san francisco", "united states", "united kingdom",
    "north america", "south africa", "hong kong", "new zealand",
    "privacy score", "files processed", "run scan", "audit report",
    "data preview", "cleaned data", "diff view",
}


def _synthetic_replacement(etype: str) -> str:
    """Return a synthetic value for the given entity type."""
    val = SYNTHETIC.get(etype, f"[{etype}]")
    if callable(val):
        return val()
    if isinstance(val, list):
        return random.choice(val)
    return val


def regex_redact_series(
    series: pd.Series,
    mode: str,
    allowlist: list[str],
) -> tuple[pd.Series, list[dict]]:
    """
    Two-pass vectorised regex sweep over an entire column.

    Pass A — collect findings per row (respects allowlist).
    Pass B — apply replacements using pandas vectorised str.replace
             (no double-redaction: we work on a fresh copy per pattern).

    Returns (cleaned_series, findings_list).
    No model involved — runs in milliseconds.
    """
    # Work on string copy; reset index so enumerate gives 0-based ints
    working = series.astype(str).reset_index(drop=True).copy()
    findings: list[dict] = []
    lower_allow = [a.lower().strip() for a in allowlist if a.strip()]

    for etype, pattern in FAST_PATTERNS.items():
        tag = TAGS.get(etype, f"[{etype}]")

        # ── Pass A: collect findings, respect allowlist ────────────────
        for ri in range(len(working)):
            val = working.iat[ri]
            if not val or val in ("nan", "None", ""):
                continue
            if lower_allow and any(a in val.lower() for a in lower_allow):
                continue
            for m in pattern.finditer(val):
                rep = (
                    tag if mode == "Redaction"
                    else _synthetic_replacement(etype)
                )
                findings.append({
                    "row":              ri,
                    "entity_type":      etype,
                    "original_preview": val[:3] + "***",
                    "replacement":      rep,
                    "confidence":       1.0,
                })

        # ── Pass B: apply replacement vectorised ──────────────────────
        if mode == "Redaction":
            # Simple fixed-string replacement — fast
            working = working.str.replace(pattern, tag, regex=True)
        else:
            # Synthetic needs a unique value per match
            working = working.apply(
                lambda x, p=pattern, et=etype: (
                    p.sub(lambda _: _synthetic_replacement(et), x)
                    if isinstance(x, str) else x
                )
            )

    return working, findings

def _merge_adjacent_entities(entities: list[dict]) -> list[dict]:
    """
    Merge consecutive entities of the same type where end of one
    touches or overlaps the start of the next.
    Fixes sub-token fragmentation e.g. 'Kings'+'ley' → 'Kingsley'.
    """
    if not entities:
        return entities

    sorted_ents = sorted(entities, key=lambda x: x["start"])
    merged = [sorted_ents[0].copy()]

    for curr in sorted_ents[1:]:
        prev = merged[-1]
        same_type = (
            TAGS.get(prev["entity_group"]) ==
            TAGS.get(curr["entity_group"])
        )
        adjacent  = curr["start"] <= prev["end"] + 1

        if same_type and adjacent:
            # Extend the previous entity to cover this one
            prev["end"]   = max(prev["end"], curr["end"])
            prev["score"] = min(prev["score"], curr["score"])
        else:
            merged.append(curr.copy())

    return merged

def _extract_context_names(text: str, existing_entities: list[dict]) -> list[dict]:
    """
    Regex sweep for names that the NER model missed.
    Looks for capitalised name patterns in known contexts.
    """
    extra = []
    for m in NAME_CONTEXT_RE.finditer(text):
        matched = (m.group(1) or m.group(2) or "").strip()
        if not matched:
            continue
        if matched.lower() in NAME_BLOCKLIST:
            continue
        # Skip if already covered by an NER entity
        start, end = m.start(), m.end()
        # Find actual name position within full match
        name_start = text.find(matched, start)
        name_end   = name_start + len(matched)
        if any(
            e["start"] <= name_start < e["end"]
            for e in existing_entities
        ):
            continue
        extra.append({
            "start":        name_start,
            "end":          name_end,
            "entity_group": "PER",
            "score":        0.75,
        })
    return extra

def redact_cell(
    text: str,
    ner,
    mode: str,
    allowlist: list[str],
    threshold: float,
) -> tuple[str, list[dict]]:
    """
    NER-based redaction for a single cell.
    Called only for columns that need semantic understanding
    (names, organisations, free-text comments).

    Returns (cleaned_text, findings).
    """
    if not text or str(text).strip() in ("nan", "None", ""):
        return text, []

    text = str(text)

    lower_allow = [a.lower().strip() for a in allowlist if a.strip()]
    if any(a in text.lower() for a in lower_allow):
        return text, []

    entities: list[dict] = [e for e in ner(text) if e["score"] >= threshold]

    entities = _merge_adjacent_entities(entities)

    entities += _extract_context_names(text, entities)

    # Address regex sweep — catches what NER misses
    for m in ADDRESS_RE.finditer(text):
        if not any(e["start"] <= m.start() < e["end"] for e in entities):
            entities.append({
                "start": m.start(), "end": m.end(),
                "entity_group": "ADDRESS", "score": 1.0,
            })

    # Numeric ID sweep
    for m in NUMERIC_ID_RE.finditer(text):
        if not any(e["start"] <= m.start() < e["end"] for e in entities):
            entities.append({
                "start": m.start(), "end": m.end(),
                "entity_group": "ADDRESS", "score": 1.0,
            })

    findings: list[dict] = []
    result = text

    for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
        text_span = text[ent["start"]:ent["end"]]   # renamed — not 'span'
        etype     = ent["entity_group"]
        rep = (
            TAGS.get(etype, f"[{etype}]")
            if mode == "Redaction"
            else _synthetic_replacement(etype)
        )
        result = result[: ent["start"]] + rep + result[ent["end"]:]
        findings.append({
            "entity_type": etype,
            "original":    text_span,
            "replacement": rep,
            "score":       round(ent["score"], 3),
        })

    return result, findings


def force_redact_cell(value: str, mode: str, force_type: str = "ADDRESS") -> tuple[str, str]:
    """
    Directly redact a cell whose column name signals forced redaction.
    Returns (replacement_value, entity_type).
    """
    if force_type == "PER":
        rep = (
            random.choice(SYNTHETIC["PER"])
            if mode == "Synthetic"
            else TAGS["PER"]
        )
        return rep, "PER"

    # Default — ADDRESS / IP
    rep = (
        random.choice(SYNTHETIC["ADDRESS"])
        if mode == "Synthetic"
        else TAGS["ADDRESS"]
    )
    return rep, "ADDRESS"


def column_force_type(col_name: str) -> str | None:
    """
    Return "ADDRESS" if the column name warrants forced redaction,
    otherwise None.
    """
    lower = col_name.lower().strip()
    if lower in IP_COL_NAMES or lower in ADDR_COL_NAMES:
        return "ADDRESS"
    if lower in NAME_COL_NAMES:       
        return "PER"
    return None