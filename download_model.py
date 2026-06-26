"""
download_model.py
Optional one-time download script.

Run this BEFORE starting the app if you want to pre-download the model
so the first Streamlit session starts instantly.

Usage (from your .bat file or terminal with venv active):
    python download_model.py

Requires HF_TOKEN to be set in the environment, exactly as in your .bat file.
"""

import os
import sys
import hashlib

MODEL_ID   = "Babelscape/wikineural-multilingual-ner"
MODEL_PATH = "./model"


def main() -> None:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print(
            "ERROR: HF_TOKEN not set.\n"
            "Run:  set HF_TOKEN=hf_xxxx   then try again."
        )
        sys.exit(1)

    print(f"Authenticating with HuggingFace Hub...")
    from huggingface_hub import login
    login(token=token, add_to_git_credential=False)

    print(f"Downloading model: {MODEL_ID}")
    print("This may take several minutes depending on your connection (~1-3 GB).")

    from transformers import AutoTokenizer, AutoModelForTokenClassification

    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    mdl = AutoModelForTokenClassification.from_pretrained(
        MODEL_ID, trust_remote_code=True
    )

    print(f"Saving model to {MODEL_PATH} ...")
    tok.save_pretrained(MODEL_PATH)
    mdl.save_pretrained(MODEL_PATH)

    # Simple integrity check — verify the config file exists
    config_path = os.path.join(MODEL_PATH, "config.json")
    if os.path.isfile(config_path):
        sha = hashlib.sha256(open(config_path, "rb").read()).hexdigest()[:12]
        print(f"Download complete. config.json SHA256 prefix: {sha}")
    else:
        print("WARNING: config.json not found — download may be incomplete.")

    print("\nDone. You can now start the app:  streamlit run app.py")


if __name__ == "__main__":
    main()