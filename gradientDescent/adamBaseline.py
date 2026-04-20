"""
AdamW Baseline Script - Matches Spectral Setup
==============================================
Runs classical AdamW on the exact same dummy task and saves loss history for comparison.
"""

import torch
import torch.nn as nn
from torch.optim import AdamW
from transformers import AutoModelForCausalLM, AutoConfig
import numpy as np

print("Initializing AdamW Baseline...\n")

config = AutoConfig.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_config(config)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

optimizer = AdamW(model.parameters(), lr=5e-5)

batch_size, seq_len = 2, 64
dummy_input = torch.randint(0, config.vocab_size, (batch_size, seq_len), device=device)
dummy_labels = dummy_input.clone()

loss_history = []

print(f"Starting AdamW training on {device} for 350 steps...\n" + "-"*90)

for step in range(350):
    model.train()
    optimizer.zero_grad()
    
    outputs = model(dummy_input, labels=dummy_labels)
    loss = outputs.loss
    
    loss.backward()
    optimizer.step()
    
    loss_history.append(loss.item())
    
    if step % 20 == 0 or step < 10 or step > 330:
        print(f"Step {step+1:03d} | Loss {loss.item():.4f}")

print("-"*90)
print(f"AdamW training complete.")
print(f"Final loss: {loss_history[-1]:.4f}")
print(f"Mean loss (last 50 steps): {np.mean(loss_history[-50:]):.4f}")

# Save for plotting
np.save('adam_loss.npy', np.array(loss_history))
print("Saved: adam_loss.npy")

print("\nYou can now run the plotting script which will automatically load both spectral and Adam data.")


# (base) brendanlynch@Brendans-Laptop gradientDescent % python adamBaseline.py
# Initializing AdamW Baseline...

# Starting AdamW training on cpu for 350 steps...
# ------------------------------------------------------------------------------------------
# `loss_type=None` was set in the config but it is unrecognized. Using the default loss: `ForCausalLMLoss`.
# Step 001 | Loss 10.9849
# Step 002 | Loss 10.1681
# Step 003 | Loss 9.7342
# Step 004 | Loss 9.2927
# Step 005 | Loss 8.9669
# Step 006 | Loss 8.6711
# Step 007 | Loss 8.4564
# Step 008 | Loss 8.1566
# Step 009 | Loss 7.9108
# Step 010 | Loss 7.7072
# Step 021 | Loss 5.2162
# Step 041 | Loss 1.9391
# Step 061 | Loss 0.5436
# Step 081 | Loss 0.2047
# Step 101 | Loss 0.1115
# Step 121 | Loss 0.0845
# Step 141 | Loss 0.0654
# Step 161 | Loss 0.0577
# Step 181 | Loss 0.0480
# Step 201 | Loss 0.0435
# Step 221 | Loss 0.0365
# Step 241 | Loss 0.0325
# Step 261 | Loss 0.0309
# Step 281 | Loss 0.0266
# Step 301 | Loss 0.0243
# Step 321 | Loss 0.0229
# Step 332 | Loss 0.0214
# Step 333 | Loss 0.0217
# Step 334 | Loss 0.0211
# Step 335 | Loss 0.0213
# Step 336 | Loss 0.0214
# Step 337 | Loss 0.0211
# Step 338 | Loss 0.0212
# Step 339 | Loss 0.0210
# Step 340 | Loss 0.0223
# Step 341 | Loss 0.0201
# Step 342 | Loss 0.0217
# Step 343 | Loss 0.0223
# Step 344 | Loss 0.0222
# Step 345 | Loss 0.0200
# Step 346 | Loss 0.0206
# Step 347 | Loss 0.0211
# Step 348 | Loss 0.0202
# Step 349 | Loss 0.0208
# Step 350 | Loss 0.0204
# ------------------------------------------------------------------------------------------
# AdamW training complete.
# Final loss: 0.0204
# Mean loss (last 50 steps): 0.0224
# Saved: adam_loss.npy

# You can now run the plotting script which will automatically load both spectral and Adam data.
# (base) brendanlynch@Brendans-Laptop gradientDescent % 
