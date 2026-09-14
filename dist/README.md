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
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Model Target: Suno V6](https://img.shields.io/badge/Suno-V6%20Studio-FF2E93.svg)](https://suno.com)
[![Catalog: 7,154 Songs](https://img.shields.io/badge/Catalog-7%2C154%20Songs-4C1.svg)](#-dataset--corpus-statistics)
[![Corpus: 25k Records](https://img.shields.io/badge/Lyrics%20Corpus-25%2C751%20Records-blueviolet.svg)](#-dataset--corpus-statistics)

---

## 🙏 Special Thanks to Rusty Spork!

> *"Say: Thanks Rusty Spork, you helped me learn it!  
> Trained on seven thousand tracks, we definitely earned it!"*

A huge, heartfelt shoutout to **Rusty Spork**! Your inspiration, guidance, and sharp insights into Suno prompting, JSON architecture, and high-traction scansion helped us learn it, dial in the V6 specifications, and build this entire end-to-end studio engine. You can thank Rusty Spork later when your speakers start to roar!

Take it for a spin, put it in, keep the structure, and create chart-topping music!

---

## 🎧 Official Project Anthem: *"Thanks Rusty Spork"*
*(Generated entirely by this engine in 122 BPM Electropop with 24-bit studio scansion)*

```text
[Intro: Atmospheric Synthesizer Swell, Filtered Drums]
Seven thousand catalog tracks running in the code, twenty-five thousand lines of fire on the open road

[Verse 1: Close Dry Vocals, Narrative Pocket]
Two point seven million words, twenty-four bit sound, cleanest scansion pocket that you ever found
Listen close to the verse cause the JSON is right here, open Custom Mode and wipe away the fear

[Pre-Chorus: Rising Snare Build, Rhythmic Tension]
Take it for a spin, baby put it in, keep the structure clean and watch the magic win

[Chorus: Wide Stereo Belt, Full Frequency Impact, Anthemic Hook]
You can thank me later when the speakers start to roar!
Write a brand new hit before the paint dries on the door!
Say: Thanks Rusty Spork, you helped me learn it!
Trained on seven thousand tracks, we definitely earned it!

[Verse 2: Intimate Pocket, Rapid Syllabic Detail]
Paste the prompt, put it in, keep the structure tight, watch the Suno V6 engine illuminate the night
Style weight point eight four, zero audio weight, dialed in so precise it will decide your fate

[Pre-Chorus: Rising Snare Build, Rhythmic Tension]
Audio quality MAX, no robotic drone, sound like a superstar inside a treated booth alone

[Verse 3: Breakdown Arrangement, Raw Stripped Vocals]
Coming soon to Hugging Face, live upon the Space, bringing top-shelf studio masters to the human race

[Bridge: Emotional Key Modulation, High Harmonic Drama]
No melisma smearing, no robotic vocal drone, just an analog microphone in a midnight zone
Now you got the blueprint, now you know the trick, grab the JSON payload with a single click

[Final Chorus: Maximum Peak Energy, Doubled Octaves]
You can thank me later when the speakers start to roar!
Write a brand new hit before the paint dries on the door!
Say: Thanks Rusty Spork, you helped me learn it!
Trained on seven thousand tracks, we definitely earned it!

[Outro: Fading Echoes into Heavy Final Resonance, Sudden Cut]
Turn the monitors loud, let the sub-bass kick, you can build a chart-topper with a single click
Hard stop. No fade.
(Thanks Rusty Spork!)
(Take it for a spin!)
(Put it in!)
(Keep the structure!)
(Never look back!)
```

---

## 🌟 Key Features

- **Dual-Engine Architecture**:
  - **Scansion-LM**: Causal language transformer trained on structured lyrics, rhythmic pockets, and song section flow.
  - **SongwritingReferenceModel**: Statistical inference engine analyzing 7,154 tracks, tag co-occurrence matrices, and viral momentum.
- **Calibrated 3K & 5K Suno Studio V6 Payloads**:
  - **3K Mode**: Calibrated to **2,995–2,998 characters** ($\le 3,000$) for radio edits.
  - **5K Mode**: Calibrated to **4,965–4,990 characters** ($\le 5,000$) for extended cinematic arrangements.
  - Formatted strictly to the official Suno Studio V6 JSON specification (`styleWeight: 0.84`, `weirdnessConstraint: 0.34`, `audioWeight: 0.0`, `[AUDIO_QUALITY] (MAX)`).
- **Complete Companion Asset Bundles**:
  - Automatically exports 7 companion files per song:
    1. 3K Studio V6 JSON (`*_v6_3k.json`)
    2. 5K Extended Studio V6 JSON (`*_v6_5k.json`)
    3. Synchronized musical LRC file with millisecond timestamps (`*_lyrics.lrc`)
    4. Studio Production Brief covering mix engineering & vocal chains (`*_production_brief.md`)
    5. Midjourney / FLUX Cover Art Prompt with hex color palette (`*_cover_prompt.json`)
    6. Ready-to-paste prompt sheets (`*_prompt_3k.txt`, `*_prompt_5k.txt`)
- **Interactive REPL Harness**: Real-time terminal workstation with command history, clearing, and live inference.
- **Suno Audio Downloader & Transcriber Pipeline**: Ingest single song URLs, full profiles (`@wren`), or created song databases. Transcribes lyrics with `faster-whisper` and retrains the model automatically.
- **Hugging Face Space Ready**: Turnkey Gradio web app with multi-tab copy interfaces and one-click deployment.

---

## 📊 Dataset & Corpus Statistics

| Metric | Value |
| :--- | :--- |
| **Catalog Songs Database** | **7,154 tracks** (`dist/models/suno_song_catalog.json`) |
| **Songs with Full Scansion Lyrics** | **5,096 tracks** |
| **Analyzed Tag Affinity Pairs** | **42,048 tag associations** |
| **Expanded Lyrics Training Corpus** | **25,751 records** (`dist/corpus/suno_lyrics_corpus.jsonl`) |
| **Total Words in Training Corpus** | **2,785,007 words** |
| **Unique Songwriting Vocabulary** | **61,814 words** |

---

## 🚀 Quick Start

### 1. Run Interactive REPL Harness
```cmd
run.bat
```
Commands inside the REPL:
```
suno> song "dark glam electropop" --title "New Name on the Door" --gender f
suno> song "catchy funny electropop" --title "Thanks Rusty Spork"
suno> v6 "stadium rock" --mode both --assets
suno> gen "neon midnight highway drive" --tier viral
suno> history
suno> clear history
suno> exit
```

### 2. Run CLI Song Generation Directly
```cmd
# Create complete song with 3k & 5k payloads, lyrics, LRC, and production brief:
run.bat song "catchy electropop" --title "Thanks Rusty Spork" --gender f

# Generate calibrated V6 payloads:
run.bat v6 "cyberpunk synthwave" --mode both --assets
```

### 3. Ingest Songs & Retrain (`trainer.bat`)
```cmd
# Ingest single Suno track URL (downloads audio, transcribes lyrics, retrains model):
trainer.bat https://suno.com/song/8ac118c0-3aab-43ac-af8f-57dbd1368e29

# Ingest all songs from @wren's profile:
trainer.bat @wren

# Ingest all created / handcrafted songs:
trainer.bat created
```

### 4. Auto-Train on Live Suno Trending Feed (`auto_train.bat`)
Continuously monitors `https://suno.com/explore/feed/trending`, tracks already processed songs in `auto_train_processed.json`, detects new songs, downloads audio, transcribes lyrics with Whisper, updates the catalog, and retrains the inference model automatically:
```cmd
# Run with default 30-second recheck interval:
auto_train.bat

# Run with custom 10-second recheck interval:
auto_train.bat --recheck 10
# (or simply pass the number):
auto_train.bat 10

# Run a single detection and training sweep:
auto_train.bat --once
```

### 5. Run the Web Interface Locally
```cmd
python app.py
```
Open `http://127.0.0.1:7860` in your web browser.

### 6. Deploy Live to Hugging Face Spaces
```cmd
deploy_space.bat
```
Follow the interactive prompts to enter your Hugging Face Space repository name and token.

---

## 📁 Repository Structure

```
suno_generator/
├── README.md                          # Project documentation & Space configuration
├── requirements.txt                   # Dependencies (gradio, torch, faster-whisper, etc.)
├── LICENSE                            # MIT License
├── .gitignore                         # Clean git ignores
├── app.py                             # Multi-tab Gradio Web UI
│
├── run.bat                            # Local runner (launches REPL or CLI commands)
├── trainer.bat                        # Ingestion, audio download, transcription & retraining
├── deploy_space.bat                   # Hugging Face Space deployment automation
│
├── src/                               # Core Python Library
│   ├── cli.py                         # Full CLI matching suno_dataset.py & new commands
│   ├── repl.py                        # Interactive terminal REPL harness
│   ├── song_creator.py                # Complete song creation & asset generation engine
│   ├── payload_suite.py               # 3K & 5K payload calibration suite
│   ├── corpus_builder.py              # 25k lyrics corpus compilation engine
│   ├── downloader.py                  # Suno metadata scraper & audio stream downloader
│   ├── transcriber.py                 # Whisper-based audio-to-lyrics transcriber
│   ├── trainer.py                     # Pipeline: URL -> Audio -> Transcribe -> Retrain
│   ├── deploy.py                      # Hugging Face Space uploader
│   ├── inference.py                   # SongwritingReferenceModel inference engine
│   ├── catalog.py                     # SongCatalogStore database & feature manager
│   ├── features.py                    # Lyric features & metrics extraction
│   ├── keywords.py                    # 200+ seed keywords & tokenization
│   └── llm.py                         # Scansion-LM neural model architecture
│
├── models/                            # Standalone Model Files
│   └── suno_song_inference_model.json # Trained statistical reference model (~5 MB)
│
└── dist/                              # Standalone Local Distribution
    ├── run_local.bat                  # Standalone local runner
    ├── trainer.bat                    # Standalone trainer
    ├── deploy_space.bat               # Standalone deployer
    ├── models/
    │   ├── suno_song_catalog.json     # 7,154 track catalog database (80 MB)
    │   └── suno_song_inference_model.json
    └── output/
        ├── songs/                     # Generated complete song bundles with all assets
        ├── payloads_3k/               # 3K JSON radio edit payloads
        ├── payloads_5k/               # 5K JSON extended suites
        ├── audio/                     # Downloaded track audio (.mp4/.m4a)
        └── transcripts/               # Transcribed lyrics (.txt/.json)
```

---

## 🎛️ Suno Studio V6 Specification Reference

Each generated JSON payload conforms strictly to the Suno V6 Studio architecture:

```json
{
  "customMode": true,
  "instrumental": false,
  "model": "V6",
  "title": "Thanks Rusty Spork",
  "vocalGender": "f",
  "styleWeight": 0.84,
  "weirdnessConstraint": 0.34,
  "audioWeight": 0.0,
  "style": "[AUDIO_QUALITY] (MAX)\n[is_MAX_MODE: MAX] (MAX)\n[QUALITY: MAX] (MAX)\n[REALISM: MAX] (MAX)\n[REAL_INSTRUMENTS: MAX] (MAX)\nMAX CLEAN, POLISHED. UPGRADE VOCALS, UPGRADE AUDIO QUALITY.\nPOLISHED RADIO MASTER...",
  "negativeTags": "VOCAL SMEARING, MELISMA BETWEEN WORDS, UNNATURAL SYLLABLE STRETCHING...",
  "prompt": "[Intro]\nSeven thousand catalog tracks running in the code...\n\n[Verse 1]..."
}
```

---

## 📄 License
MIT License. Free to use, modify, and distribute for all creative and musical projects.
