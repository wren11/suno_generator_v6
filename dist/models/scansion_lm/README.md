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

# 🏭 Scansion-LM Foundry

A high-performance causal language modeling harness that learns rhyme density, poetic scansion, and structured lyric progressions for Suno Custom Mode.

Fine-tuned from `distilgpt2` on clean, original lyric extracts. The model produces natural English rhythmic lines conforming to Suno Studio V6 scansion rules.

---

## ⚡ Quick Start

### 1. Launch Loopback HTTP Sidecar (Port 8099)
```powershell
.\run-engine.cmd
```
*Hosts the loopback server on `http://127.0.0.1:8099`, automatically connecting to Scansion Studio Web UI.*

### 2. Command Line Pipeline Operations
```powershell
# Extract meter, rhyme schemes, and sections
python -m scansion_lm extract 640

# Tokenize corpus using Hugging Face AutoTokenizer
python -m scansion_lm tokenize

# Fine-tune causal language model
python -m scansion_lm train 300 640

# Evaluate against gold standard metric sheet
python -m scansion_lm eval

# Verify weights and model card readiness
python -m scansion_lm check

# Export model bundle for Hugging Face Hub
python -m scansion_lm export
```

---

## 📡 Sidecar HTTP API Endpoints (Port 8099)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Instant readiness and training state probe |
| `GET` | `/status` | Phase, step count, loss, and training process ID |
| `GET` | `/metrics` | Real-time training loss and validation progression |
| `GET` | `/trending` | Returns cached Suno trending metadata and tags |
| `POST` | `/ingest-batch` | Batch ingests new song lyrics into `user_extracts.jsonl` |
| `POST` | `/train` | Spawns background fine-tuning process |
| `POST` | `/infer` | Autoregressive lyric generation from idea/theme |
| `POST` | `/extract` | Scans input lyrics for feet, meter, and rhyme scheme |

---

## 🧠 Model Architecture

| Component | Specification |
|---|---|
| Base Architecture | `distilgpt2` (`GPT2LMHeadModel`) |
| Parameters | 81,912,576 (81.9M) |
| Vocabulary Size | 50,257 tokens (GPT-2 BPE) |
| Context Length | 1,024 tokens (256 training window) |
| Storage Format | `safetensors` (zero pickle vulnerability) |
| Checkpoint Size | ~327 MB |

---

## 📄 License

Licensed under the **Apache 2.0 License**. See `LICENSE` for details.


## Checkpoint

- architecture: `['GPT2LMHeadModel']`
- vocab_size: `50260`
- n_positions: `1024`
- n_layer / n_embd / n_head: `6 / 768 / 12`
- parameters: `81914880`
- steps: `300/300`
- train loss (avg): `4.009729862213135`
- examples: `3500`

Load with vanilla Transformers — no custom `auto_map`:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
tok = AutoTokenizer.from_pretrained("scansion-lm")
model = AutoModelForCausalLM.from_pretrained("scansion-lm")
prompt = """Title: Heat Line
Idea: A man scraping survival out of desert heat, stubborn will over panic.
Verse:
"""
ids = tok(prompt, return_tensors="pt")
out = model.generate(**ids, max_new_tokens=80, do_sample=True, temperature=0.85,
                    pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id)
print(tok.decode(out[0], skip_special_tokens=False))
```

Upload:

```bash
huggingface-cli upload ./export scansion-lm --repo-type model
```
