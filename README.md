---
title: Suno AI Song Generator & Reference Model
emoji: 🎵
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🎵 Suno AI Song Generator & Reference Model
### *High-Traction Studio V6 Songwriting Inference Engine & Interactive REPL Harness*

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces)
[![GitHub Actions CI/CD](https://img.shields.io/badge/GitHub%20Actions-Deploy%20to%20HF-success)](https://github.com/wren11/suno_generator_v6/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Model Target: Suno V6](https://img.shields.io/badge/Suno-V6%20Studio-FF2E93.svg)](https://suno.com)
[![Catalog: 9,075+ Songs](https://img.shields.io/badge/Catalog-9%2C075%2B%20Songs-4C1.svg)](#-dataset--corpus-statistics)
[![Corpus: 30.8MB JSONL](https://img.shields.io/badge/Lyrics%20Corpus-30.8%20MB%20Scansion-blueviolet.svg)](#-dataset--corpus-statistics)
[![Hardware: Multi-GPU / SLI](https://img.shields.io/badge/Hardware-Dual%20RTX%202080%20SLI%20Ready-76B900.svg)](#-multi-gpu--rtx-2080-sli-hardware-acceleration)

---

## ⚡ Quickstart — 2 Single Scripts for Everything

No complicated setup, no duplicate output directories, and zero code edits required. Everything runs from two single `.bat` scripts:

```
======================================================================
  ____  _   _ _   _  ___     ____ _____ _   _ _____ ____     _  _____ ___  ____  
 / ___|| | | | \ | |/ _ \   / ___| ____| \ | | ____|  _ \   / \|_   _/ _ \|  _ \ 
 \___ \| | | |  \| | | | | | |  _|  _| |  \| |  _| | |_) | / _ \ | || | | | |_) |
  ___) | |_| | |\  | |_| | | |_| | |___| |\  | |___|  _ < / ___ \| || |_| |  _ < 
 |____/ \___/|_| \_|\___/   \____|_____|_| \_|_____|_| \_/_/   \_\_| \___/|_| \_\

  Suno AI Songwriting Reference Model & Interactive REPL Harness v2.0
======================================================================
```

---

### 🎮 1. `run.bat` — Run the Studio, Wizard, or CLI
Double-click `run.bat` (or run in your terminal):
```powershell
# Launch interactive REPL with Wizard, live trending, and hit generator:
.\run.bat

# Or pass CLI arguments directly:
.\run.bat wizard
.\run.bat song "cyberpunk synthwave future hacker" --title "NEON PULSE" --bpm 128
```

#### Inside the Interactive REPL:
- `wizard` — Interactive step-by-step Hit Song Creation Wizard.
- `song <theme>` — Generates a complete 3K & 5K Suno V6 payload, 1024x1024 cover art, and 10s teaser video into `output/songs/`.
- `trending` — Browse live trending tracks from Suno.com (use `trending --train` to retrain).
- `suggest` — Suggest viral tags and high-traction style packs.
- `cover <title>` — Render custom album cover art with text overlays.
- `video <cover_png>` — Render 10-second tempo-synced video teaser.
- `help` — List all documented commands.

---

### 🎓 2. `train.bat` — Train the Model & Expand the Corpus
Double-click `train.bat` (or run in your terminal):
```powershell
# Default (no arguments): Auto-train from live Suno.com trending songs
.\train.bat

# Ingest a specific Suno song URL (downloads audio, transcribes with Whisper, retrains):
.\train.bat "https://suno.com/song/<song-id>"

# Ingest an entire creator profile:
.\train.bat @wren

# Ingest handcrafted prompt archives and created songs:
.\train.bat created
```

*Every trained or generated track automatically appends lyrics and scansion patterns to `corpus/suno_lyrics_corpus.jsonl`, updates `models/suno_song_catalog.json`, and retrains the reference model.*

---

## 🧠 Always-On Neural LLM & Corpus Auto-Learning

1. **Default LLM Generation**: The system always uses the neural Scansion-LM and studio LLM engine by default across CLI, REPL, and Wizard.
2. **Continuous Corpus Growth**: Every song generated or ingested is automatically analyzed:
   - Full song sheets formatted with `<|brief|> ... <|sheet|> ... <|end|>` tokens.
   - Section-by-section scansion continuations extracted into `corpus/suno_lyrics_corpus.jsonl`.
   - New tracks registered in `models/suno_song_catalog.json` (9,075+ songs) and retrained in `models/suno_song_inference_model.json`.
3. **100% Anti-AI Cliché Enforcement**: Purges generic words (*neon, tapestry, whispers, echoes, ignite, shadows, labyrinth, beacon, abyss, ethereal, celestial*).
4. **Prompt Constraint Detection**: Automatically extracts lipograms (e.g., *without letter e*) and custom lyrical directives directly from your prompt.

---

## 📁 Clean Output Structure

All outputs are written to a single canonical directory:
```
output/
├── songs/         # Generated song folders (JSON payloads, LRC lyrics, production briefs)
├── covers/        # Generated 1024x1024 album covers (PNG & JPG)
├── prompts/       # Paste-ready Suno prompt seeds
├── payloads_3k/   # 3K Suno Studio V6 API payloads
├── payloads_5k/   # 5K Extended Suno Studio V6 API payloads
├── audio/         # Downloaded training audio streams
└── transcripts/   # Transcribed Whisper lyrics & timestamp alignments
```

---

## 🎨 Album Cover Art & 10s Teaser Video Studio

Every song generation automatically creates multi-media assets:

### 1. High-Resolution Cover Art (1024x1024 PNG + JPG)
- **Genre-Tuned Visual Palettes**: Cyberpunk neon, dark glam synthwave, vintage lo-fi, trap midnight, and acoustic warm gold.
- **Custom Studio Typography**: Render your exact song title, artist persona, and custom badge (`DELUXE`, `RADIO MASTER`).
- **Base Image URL Referencing**: Pass any public image URL via `--ref <url>` to use as a starting canvas.
- **AI Art Prompts**: Generates a dedicated `*_cover_prompt.txt` optimized for Midjourney, DALL-E 3, and Stable Diffusion.

### 2. 10-Second Teaser Video (`teaser_10s.mp4`)
- **1080x1080 Square Format**: Ready for Instagram Reels, TikTok, YouTube Shorts, and X/Twitter.
- **Cinematic Ken Burns Effect**: Smooth camera zoom centered on the album artwork.
- **Beat-Synchronized Audio**: Generates an acoustic/synth audio pulse matching your exact BPM.

---

## ⚡ Multi-GPU & RTX 2080 SLI Hardware Acceleration

The engine includes built-in hardware topology detection (`src/hardware.py`):
- **Auto-Detection**: Identifies dual NVIDIA GPUs (e.g. 2x NVIDIA GeForce RTX 2080) and detects SLI / NVLink links.
- **Distributed Inference & Training**: Supports PyTorch `DistributedDataParallel` and `DataParallel` across multiple GPUs.
- **Hardware Status Check**:
  ```powershell
  python -c "import src.hardware; src.hardware.print_hardware_report()"
  ```

---

## 🚀 Automated Deployment to Hugging Face (GitHub Actions)

When you commit or push to GitHub, the included release workflow automatically packages and deploys the entire model and Space to Hugging Face!

### Setup in 30 Seconds:
1. Go to your repository on GitHub: **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret**.
3. Name: `HFKEY`
4. Value: *Paste your Hugging Face write token* (from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).
5. Click **Add secret**.

Every push to `main` deploys the live interactive Gradio Studio Space at `https://huggingface.co/spaces/<your-username>/suno-generator-v6`.

---

## 📊 Dataset & Model Statistics

- **Catalog Songs**: **9,075+ tracks** cataloged with complete metadata, play counts, and like counts.
- **Training Corpus**: **30.8 MB** compiled lyrical scansion dataset (`corpus/suno_lyrics_corpus.jsonl`).
- **Scansion Patterns**: **670+ structural progressions** (verse-chorus-bridge mappings).
- **Tag Traction Scoring**: **45,800+ indexed musical tags** ranked by real viral performance.
- **Scansion-LM**: 81.9M parameter causal LM fine-tuned on rhyme density and meter scansion.

---

## 📜 REPL Command Reference

| Command | Description | Example |
|---|---|---|
| `wizard` | Step-by-step interactive song creation wizard | `wizard` |
| `song <theme>` | Generate a full 3K/5K song bundle + cover + video | `song "viral anthem" --title "HEAT" --bpm 140` |
| `trending` | View live trending songs from Suno.com (`--train` to retrain) | `trending --train` |
| `suggest` | Style packs & viral tag suggestions from learned data | `suggest --theme "dark pop"` |
| `train <url>` | Ingest Suno URL, download audio, transcribe, retrain | `train "https://suno.com/song/<id>"` |
| `cover <title>` | Generate standalone album cover art | `cover "CYBER WIFE" --genre "electropop"` |
| `video <cover>` | Render standalone 10s teaser video from image | `video output/covers/cover.png --bpm 128` |
| `stats` | Display catalog metrics, traction scores, and LM state | `stats` |
| `batch <theme>`| Generate multiple creative variations | `batch "phonk drift" --n 5` |
| `help` | Show interactive help and documentation | `help` |
| `exit` | Exit the REPL session | `exit` |

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
