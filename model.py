"""
model.py
Loads and caches the PII NER model.

Authentication:
    Reads HF_TOKEN from the environment variable set in your .bat file.

Model:
    Babelscape/wikineural-multilingual-ner
    278 MB, multilingual, purpose-built NER — 5-10x faster than MoE on CPU.

Inference runtime:
    ONNX path  (./model_onnx) — used if present, 2-3x faster than PyTorch
    PyTorch path (./model)    — fallback if ONNX conversion not yet done

Caching:
    @st.cache_resource loads the model exactly once per session.
    Re-uploading a file does NOT reload the model.
"""

import os
import torch
import streamlit as st
from huggingface_hub import login
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

MODEL_ID      = "Babelscape/wikineural-multilingual-ner"
MODEL_PATH    = "./model"       # PyTorch weights — downloaded on first run
ONNX_PATH     = "./model_onnx"  # ONNX weights  — created by convert_to_onnx.py


def _authenticate() -> None:
    """Log in to HuggingFace Hub using the token from the environment."""
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        st.error(
            "HF_TOKEN environment variable is not set. "
            "Add it to your .bat file:  set HF_TOKEN=hf_xxxx"
        )
        st.stop()
    login(token=token, add_to_git_credential=False)


@st.cache_resource(show_spinner=False)
def load_model():
    """
    Load the NER pipeline. Priority:
      1. ONNX runtime  (./model_onnx) — fastest, use after running convert_to_onnx.py
      2. PyTorch       (./model)      — fast, used on first run or before ONNX conversion
      3. HuggingFace Hub              — downloaded on very first run, saved to ./model
    """
    _authenticate()

    # ── ONNX path (fastest) ───────────────────────────────────────────
    if os.path.isdir(ONNX_PATH):
        try:
            from optimum.onnxruntime import ORTModelForTokenClassification
            tok = AutoTokenizer.from_pretrained(ONNX_PATH)
            mdl = ORTModelForTokenClassification.from_pretrained(ONNX_PATH)
            return pipeline(
                "ner",
                model=mdl,
                tokenizer=tok,
                aggregation_strategy="first",
                batch_size=64,
            )
        except ImportError:
            # optimum not installed — fall through to PyTorch path
            pass

    # ── PyTorch path ──────────────────────────────────────────────────
    source = MODEL_PATH if os.path.isdir(MODEL_PATH) else MODEL_ID

    tok = AutoTokenizer.from_pretrained(source, trust_remote_code=True)
    mdl = AutoModelForTokenClassification.from_pretrained(
        source,
        trust_remote_code=True,
        torch_dtype=torch.float32,  # float32 is faster than float16 on CPU
    )
    mdl.eval()

    # Save locally so subsequent runs skip the Hub download
    if source == MODEL_ID:
        tok.save_pretrained(MODEL_PATH)
        mdl.save_pretrained(MODEL_PATH)

    return pipeline(
        "ner",
        model=mdl,
        tokenizer=tok,
        aggregation_strategy="first",
        device=-1,      # force CPU
        batch_size=64,  # model is small — large batches are efficient
        num_workers=0,  # avoid multiprocessing overhead on Windows
    )