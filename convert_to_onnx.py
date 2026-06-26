# convert_to_onnx.py
import os
from optimum.onnxruntime import ORTModelForTokenClassification
from transformers import AutoTokenizer

# Set the correct model ID
MODEL_ID = "Babelscape/wikineural-multilingual-ner"
ONNX_PATH = "./model_onnx"

print(f"🔄 Fetching and converting {MODEL_ID} to ONNX format...")
print("Compiling the neural network graph for optimized CPU execution. Please wait...")

# Standard models can be exported directly using the model ID string
model = ORTModelForTokenClassification.from_pretrained(MODEL_ID, export=True)
tok = AutoTokenizer.from_pretrained(MODEL_ID)

# Save the optimized binaries locally
model.save_pretrained(ONNX_PATH)
tok.save_pretrained(ONNX_PATH)

print(f"✅ Success! Optimized ONNX model files are saved in: {ONNX_PATH}")
print("You can now safely delete this script.")