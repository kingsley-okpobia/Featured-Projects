<div align="center">

<img src="https://img.shields.io/badge/PrivacyGuard_UI-Local_PII_Redaction-0F172A?style=for-the-badge&logo=shield&logoColor=white" alt="PrivacyGuard UI"/>

```
██████╗ ██████╗ ██╗██╗   ██╗ █████╗  ██████╗██╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
██╔══██╗██╔══██╗██║██║   ██║██╔══██╗██╔════╝╚██╗ ██╔╝██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
██████╔╝██████╔╝██║██║   ██║███████║██║      ╚████╔╝ ██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██╔═══╝ ██╔══██╗██║╚██╗ ██╔╝██╔══██║██║       ╚██╔╝  ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
██║     ██║  ██║██║ ╚████╔╝ ██║  ██║╚██████╗   ██║   ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
```

### **Local PII Redaction · Zero Data Egress · 16 Languages · GDPR / HIPAA / CCPA Ready**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co)
[![ONNX](https://img.shields.io/badge/ONNX-Runtime-005CED?style=flat-square&logo=onnx&logoColor=white)](https://onnxruntime.ai)
[![Phoenix](https://img.shields.io/badge/Arize-Phoenix-6366F1?style=flat-square)](https://phoenix.arize.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)

<br/>

> **Every PII redaction happens on your machine. Your data never leaves.**

<br/>

</div>

---

## What is PrivacyGuard UI?

PrivacyGuard UI is a **local-first PII redaction platform** that detects and removes personally identifiable information from CSV and JSON datasets — entirely on your machine, with zero cloud calls. Built for compliance officers, data scientists, and developers who need audit-ready data sanitisation without sending sensitive data to external APIs.

It wraps a purpose-built multilingual NER model in a clean, Lovable-designed interface and uses a two-pass architecture — vectorised regex for structured PII, neural NER for semantic entities — to achieve **sub-60-second processing for 10,000-row datasets on a standard CPU**.

---

## Key Features

| Feature | Detail |
|---|---|
| 🔒 **Zero data egress** | All inference runs locally. No cloud API calls. No data leaves your machine. |
| ⚡ **Two-pass architecture** | Vectorised regex handles emails, phones, IPs instantly. NER model handles names, orgs, free text. |
| 🌍 **16 languages** | English, French, Spanish, German, Japanese, Portuguese, Italian, Dutch, Polish, Russian, Chinese (Simplified), Arabic, Korean, Turkish, Swedish, Hindi |
| 📋 **Audit trail** | Every redaction exported as a structured audit CSV with entity type, confidence score, and action taken |
| 🔄 **Two redaction modes** | **Redaction** — replace with tags `[NAME]`, `[EMAIL]`. **Synthetic** — replace with realistic fake data |
| 📊 **Privacy Score** | Session-level score (0–100) with per-entity-type breakdown |
| 🔍 **Diff view** | Side-by-side original vs redacted comparison before export |
| 🧠 **LLM Observability** | Arize Phoenix integration for model evaluation and trace analysis |
| 📁 **CSV + JSON** | Flat CSV and nested JSON (one level deep, dot-notation flattening) |
| 🎛️ **Column picker** | Auto-detects PII-likely columns. Full manual override. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        app.py  (entry point)                     │
│                    orchestration only · no business logic         │
└──────┬──────────────┬──────────────┬─────────────┬──────────────┘
       │              │              │             │
  ┌────▼────┐   ┌─────▼─────┐  ┌───▼───┐   ┌────▼────────┐
  │sidebar  │   │main_panel │  │state  │   │file_parser  │
  │.py      │   │.py        │  │.py    │   │.py          │
  └─────────┘   └───────────┘  └───────┘   └─────────────┘
                                                    │
              ┌─────────────────────────────────────┘
              │
  ┌───────────▼──────────────────────────────────────────────────┐
  │                      scanner.py                               │
  │                                                               │
  │  Pass 1: Vectorised regex sweep (FAST_PATTERNS)               │
  │    └─ emails · phones · IPs · dates · postcodes · cards       │
  │                                                               │
  │  Pass 2: NER model (semantic entities only)                   │
  │    └─ names · organisations · addresses · free text           │
  └──────────┬────────────────────────┬─────────────────────────┘
             │                        │
     ┌───────▼───────┐        ┌───────▼───────┐
     │ redaction.py  │        │   model.py    │
     │               │        │               │
     │ TAGS dict     │        │ ONNX path     │
     │ SYNTHETIC pool│        │ (./model_onnx)│
     │ regex patterns│        │               │
     │ _merge_entities│       │ PyTorch path  │
     └───────────────┘        │ (./model)     │
                              └───────────────┘
```

### Two-pass scanning performance

| Dataset size | Regex pass | NER pass | Total (CPU) |
|---|---|---|---|
| 1,000 rows · 5 cols | < 1s | ~3s | ~4s |
| 10,000 rows · 5 cols | ~2s | ~40s | ~42s |
| 50,000 rows · 5 cols | ~8s | ~3.5min | ~4min |

> Approximately **65% of cells** in typical business datasets are handled by the regex pass and never reach the NER model.

---

## Detected Entity Types

| Tag | Entity | Detection method |
|---|---|---|
| `[NAME]` | First, last, middle names | NER model |
| `[EMAIL]` | Email addresses | Regex + NER |
| `[PHONE]` | Phone numbers (intl. formats) | Regex + NER |
| `[ADDRESS]` | Street addresses | Regex + NER |
| `[IPADDRESS]` | IPv4 addresses | Regex |
| `[DATE]` | Date formats | Regex + NER |
| `[CREDITCARD]` | Card numbers | Regex |
| `[POSTCODE]` | Postcodes / ZIP codes | Regex |
| `[ORG]` | Organisations | NER model |
| `[ID]` | Miscellaneous identifiers | NER model |

---

## Quick Start

### Prerequisites

- Python 3.9+
- [Conda](https://docs.conda.io) (recommended) or Python venv
- HuggingFace account + access token → [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- 8 GB RAM minimum · No GPU required

### 1. Clone the repository

```bash
git clone https://github.com/kingsley-okpobia/Featured-Projects.git
cd Featured-Projects/privacyguard-backend
```

### 2. Create and activate environment

```bash
# Option A — conda (recommended)
conda create -n privacyguard python=3.11
conda activate privacyguard

# Option B — venv
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your HuggingFace token

**Windows** — edit `run_app.bat` and replace `hf_xxxx`:
```bat
set HF_TOKEN=hf_your_actual_token_here
```

**macOS / Linux**:
```bash
export HF_TOKEN=hf_your_actual_token_here
```

### 5. Download the model (first run only)

```bash
python download_model.py
```

The model (`Babelscape/wikineural-multilingual-ner`, 278 MB) downloads to `./model`. Subsequent runs use the local cache.

### 6. Run the app

**Windows:**
```bat
run_app.bat
```

**macOS / Linux:**
```bash
streamlit run app.py --server.port 8501
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Optional: ONNX Acceleration (2–3× faster on CPU)

Convert the model to ONNX format once for faster CPU inference:

```bash
pip install optimum[onnxruntime]
python convert_to_onnx.py
```

The app automatically detects `./model_onnx` and uses the ONNX runtime on next startup. No configuration needed.

---

## Optional: LLM Observability with Arize Phoenix

PrivacyGuard UI includes built-in tracing via [Arize Phoenix](https://phoenix.arize.com) for model evaluation and scan monitoring.

```bash
pip install arize-phoenix opentelemetry-sdk opentelemetry-exporter-otlp
```

Phoenix launches automatically when the app starts and opens at [http://localhost:6006](http://localhost:6006). Each scan generates one span per column — entity types detected, confidence scores, and scan duration.

---

## Project Structure

```
privacyguard-ui/
├── app.py                # Entry point — orchestration only
├── model.py              # NER model loading + ONNX/PyTorch path selection
├── redaction.py          # PII detection logic, regex patterns, synthetic pools
├── scanner.py            # Two-pass scan loop orchestration
├── file_parser.py        # CSV + JSON ingestion and validation
├── sidebar.py            # Sidebar UI component
├── main_panel.py         # Main panel UI components
├── state.py              # Session state initialisation and reset
├── styles.py             # CSS design tokens (matched to Lovable prototype)
├── download_model.py     # One-time model download script
├── convert_to_onnx.py    # One-time ONNX conversion script
├── requirements.txt      # Pinned dependencies
├── run_app.bat           # Windows launch script
└── model/                # Downloaded model weights (git-ignored)
    └── model_onnx/       # ONNX converted weights (git-ignored)
```

---

## Configuration

All configuration lives in environment variables set in `run_app.bat` (Windows) or your shell:

| Variable | Required | Description |
|---|---|---|
| `HF_TOKEN` | Yes | HuggingFace access token for model download |
| `ENV` | No | `development` enables debug logging |
| `STREAMLIT_SERVER_FILE_WATCHER_TYPE` | No | Set to `none` to suppress transformers module scan warnings |

---

## How It Works

### Redaction modes

**Redaction mode** replaces detected PII with typed tags:
```
"John Smith lives at 42 Oak Avenue, email john@example.com"
→ "[NAME] lives at [ADDRESS], email [EMAIL]"
```

**Synthetic mode** replaces PII with realistic fake equivalents:
```
"John Smith lives at 42 Oak Avenue, email john@example.com"
→ "Maria Garcia lives at 456 River Road, email user_7823@example.com"
```

### Detection sensitivity

| Setting | Threshold | Use case |
|---|---|---|
| Standard | 0.80 | High precision — clear, unambiguous PII only |
| High *(default)* | 0.60 | Balanced — recommended for most compliance use cases |
| Maximum | 0.50 | Maximum recall — review results before distributing |

### Column auto-detection

Columns are automatically pre-selected for scanning if their name contains: `name`, `email`, `phone`, `address`, `comment`, `note`, or `ip`. All selections can be manually overridden.

### Force-redact columns

Columns named `address`, `ip address`, `ip_address`, or similar are **force-redacted** — every non-empty cell is replaced without model inference, regardless of confidence.

---

## Compliance and Privacy

- **Zero egress architecture** — the application binds to `localhost` by default. No data reaches any external endpoint at any point.
- **No telemetry** — PrivacyGuard UI does not collect usage data, crash reports, or any form of analytics.
- **Audit trail** — every redaction session produces a downloadable audit CSV containing: column name, row index, original value preview (first 3 characters + `***`), entity type, confidence score, and action taken. This is designed to satisfy GDPR Article 30 record-keeping requirements.
- **Temporary files** — uploaded files are processed in memory and never written to disk outside the session.
- **Dependency SBOM** — all dependency versions are pinned in `requirements.txt`. Run `pip-audit` against this file to check for known vulnerabilities.

---

## Requirements

```
streamlit==1.35.0
transformers==4.41.0
torch==2.3.0
accelerate==0.30.0
sentencepiece==0.2.0
pandas==2.2.2
huggingface_hub
arize-phoenix          # optional — LLM observability
optimum[onnxruntime]   # optional — ONNX acceleration
opentelemetry-sdk      # optional — tracing
opentelemetry-exporter-otlp  # optional — tracing
```

---

## Known Limitations

- **File size cap** — files over 50 MB are rejected at upload. For larger datasets, split into chunks before processing.
- **Nested JSON** — only one level of nesting is flattened. Deeply nested structures are not supported in v1.1.
- **Multilingual accuracy** — the wikineural model performs best on English, French, Spanish, and German. Accuracy on Arabic, Korean, and Hindi is lower; treat results as requiring human review.
- **Regex false positives** — the regex pre-filter has no semantic understanding. Version numbers matching date patterns (`12.5.2023`) or product codes matching phone patterns may be incorrectly flagged. The allowlist and diff view are the mitigation for this.
- **Streamlit CSS stability** — the UI uses `data-testid` attribute overrides for styling. Streamlit version updates may require CSS adjustments. Do not upgrade Streamlit without running a UI regression check.

---

## Roadmap

- [ ] **v1.2** — FastAPI backend + Lovable React frontend integration
- [ ] **v1.2** — Batch queue for multiple file processing
- [ ] **v1.3** — `.xlsx` and `.txt` file support
- [ ] **v1.3** — Per-entity-type mode selection (redact names, synthesise emails)
- [ ] **v2.0** — Fine-tuned model on domain-specific PII (medical record numbers, financial IDs)
- [ ] **v2.0** — Docker image with offline model bundle for air-gapped environments
- [ ] **v2.0** — ONNX model as default (eliminating PyTorch dependency for inference)

---

## Contributing

Pull requests are welcome. For significant changes, open an issue first to discuss what you'd like to change.

```bash
# Run syntax checks across all modules
python -c "
import ast, sys
files = ['app.py','model.py','redaction.py','scanner.py',
         'file_parser.py','sidebar.py','main_panel.py','state.py']
for f in files:
    try:
        ast.parse(open(f).read())
        print(f'OK  {f}')
    except SyntaxError as e:
        print(f'ERR {f}: {e}')
        sys.exit(1)
"
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with [Streamlit](https://streamlit.io) · [HuggingFace Transformers](https://huggingface.co) · [Arize Phoenix](https://phoenix.arize.com) · [Lovable](https://lovable.dev)

**PrivacyGuard UI — because your data should stay yours.**

</div>