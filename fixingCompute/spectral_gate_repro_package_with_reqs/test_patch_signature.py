import torch
from transformers import LlamaForCausalLM, AutoTokenizer
import os, sys
# quick test that model.forward accepts kappa_x kwarg without raising
try:
    model_id = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tok = tokenizer('Hello world', return_tensors='pt')
    model = LlamaForCausalLM.from_pretrained(model_id, low_cpu_mem_usage=True)
    model.eval()
    # call forward with kappa_x kwarg
    out = model(input_ids=tok.input_ids, kappa_x=0.5)
    print('OK - model accepted kappa_x; output keys:', out.keys() if hasattr(out, 'keys') else type(out))
except Exception as e:
    print('ERROR - model did not accept kappa_x kwarg:', e)
