---
language:
  - en
license: apache-2.0
library_name: transformers
pipeline_tag: text-generation
base_model: distilgpt2
tags:
  - gpt2
  - lyrics
  - suno
  - music
  - scansion
  - text-generation
widget:
  - text: "Title: Heat Line\nIdea: A man scraping survival out of desert heat, stubborn will over panic.\nVerse:\n"
    example_title: Desert verse
  - text: "Title: As It Stays\nIdea: Driving the empty freeway after a fight you cannot unsay.\nChorus:\n"
    example_title: Night chorus
---

# 🎵 Scansion-LM Model Checkpoint

Causal language transformer model fine-tuned for high-traction songwriting scansion, rhythmic pockets, and Suno V6 lyric generation.

## 🚀 Usage with Transformers

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_path = "models/scansion_lm"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

prompt = "Title: Neo Drive\nIdea: Fast midnight cyberpunk highway chase.\nVerse:\n"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=120, temperature=0.85, top_p=0.92, do_sample=True)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 📊 Checkpoint Details
- **Architecture**: `GPT2LMHeadModel` (6 layers, 768-d, 12 attention heads)
- **Parameters**: 81.9M
- **Format**: `model.safetensors`
- **Context Window**: 1024
