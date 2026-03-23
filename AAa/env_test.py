import sys
import torch
import numpy
from transformers import AutoModelForCausalLM, AutoTokenizer

print("--- Dependency Test: SUCCESS ---")
print(f"Python Version: {sys.version}")
print(f"Torch Available: {torch.backends.mps.is_available()}")
print("--- END TEST ---")