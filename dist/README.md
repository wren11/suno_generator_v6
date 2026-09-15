---
title: Suno AI Song Generator & Reference Model
emoji: 🎵
colorFrom: yellow
colorTo: orange
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# Suno AI Song Generator & Reference Model (v6)

Inference engine, lyric scansion pipeline, and asset generator for [Suno AI](https://suno.com). Generates full 3,000 and 5,000-character Studio V6 payloads, synchronized `.lrc` lyric files, AI album artwork, and 1080p teaser videos.

- **Hugging Face Space**: [wren11ws/suno_prompt_generator_v6](https://huggingface.co/spaces/wren11ws/suno_prompt_generator_v6)
- **Live Song Examples on Suno**:
  - [PERFECT - by WREN](https://suno.com/song/7fc6893c-5764-47b9-9ba7-abef7120ab0e)
  - [BITTER TASTE - by WREN](https://suno.com/song/8ac118c0-3aab-43ac-af8f-57dbd1368e29)

---

## Output Bundle

Each generation produces a complete release package in `output/songs/<slug>/`:

| File | Description |
|---|---|
| `<slug>_payload_3k.json` | 3,000-character payload (`title`, `style`, `prompt`, `negativeTags`) |
| `<slug>_payload_5k.json` | 5,000-character extended studio payload with structural section markers |
| `<slug>_prompt_3k.txt` | Raw prompt text formatted for direct paste into Suno web UI |
| `<slug>_lyrics.lrc` | Synchronized lyric timestamps (compatible with DAWs and players) |
| `<slug>_cover.png` / `.jpg` | 1024x1024 album cover art with genre badge placed in the bottom right corner |
| `<slug>_teaser_10s.mp4` | 1080p Ultra HD (1920x1080 @ 60fps) teaser video with BPM-synced audio |
| `<slug>_cover_prompt.txt` | Prompt used for diffusion image generation |
| `<slug>_production_brief.md` | Mix specifications, target LUFS, vocal chain, and arrangement breakdown |

---

## Prerequisites & Installation

- Python 3.10 or higher
- [ffmpeg](https://ffmpeg.org/) installed and available in system `PATH` (for teaser video rendering)

```bash
git clone https://github.com/wren11/suno_generator_v6.git
cd suno_generator_v6
pip install -r requirements.txt
```

On Windows, `run.bat` and `train.bat` handle virtual environment detection and execution automatically.

---

## Usage

### 1. Command-Line Generation

Generate a full song bundle:

```bash
python -m src.song_creator "dark electro-pop anthem about digital isolation" --title "CHROME PULSE" --bpm 128 --vocal f
```

Windows shortcut:
```cmd
run.bat song "dark electro-pop anthem about digital isolation" --title "CHROME PULSE" --bpm 128 --vocal f
```

#### CLI Options

| Argument | Description | Default |
|---|---|---|
| `theme` | Musical style, genre, or lyrical prompt | *(Required)* |
| `--title`, `-t` | Song title (auto-derived from theme if omitted) | `""` |
| `--vocal`, `-v` | Vocal gender: `m` or `f` | `m` |
| `--bpm`, `-b` | Tempo in beats per minute | `140` |
| `--text`, `-tx` | Custom badge/text overlay on the album cover | `""` |
| `--ref`, `-r` | Reference image URL or local path for album artwork | `""` |
| `--image-prompt`, `-ip` | Custom visual prompt for AI diffusion artwork | `""` |
| `--no-video` | Skip rendering the 10-second MP4 teaser | `False` |
| `--lyrics`, `-l` | Custom lyrics string | `""` |
| `--lyrics-file`, `-lf` | Path to custom text file containing lyrics | `""` |
| `--lipogram` | Omit specific letters from lyrics (e.g. `e`) | `""` |
| `--engine` | Generation engine: `llm`, `reference`, `hybrid`, `dynamic` | `llm` |
| `--out-dir`, `-o` | Output directory | `output/songs` |

---

### 2. Interactive REPL

Start the interactive terminal environment:

```bash
python -m src.cli repl
```

Windows shortcut:
```cmd
run.bat
```

#### Available REPL Commands

- `wizard` — Guided step-by-step song generator (prompts for genre, title, tempo, vocal type).
- `song <theme> [flags]` — Generate a complete song bundle.
- `trending` — Fetch current trending songs from Suno.com explore feed (`trending --train` to retrain).
- `suggest --theme <genre>` — Query learned database for viral tag combinations and scansion patterns.
- `cover <title> [--genre <g>]` — Render album cover art.
- `video <cover_path> [--bpm <b>]` — Render 1080p 10-second teaser video.
- `stats` — Display catalog count, corpus size, and model state.
- `help` — Show help for all commands.

---

### 3. Training & Dataset Pipeline

The model learns from cataloged tracks, extracting lyrical structures, rhyme density, and tag co-occurrence metrics.

#### Ingest Suno Tracks
Ingest individual song URLs or creator profiles (downloads audio, transcribes with Whisper, extracts scansion records):

```bash
# Ingest specific song URL:
python -m src.trainer "https://suno.com/song/7fc6893c-5764-47b9-9ba7-abef7120ab0e"

# Ingest creator profile:
python -m src.trainer @wren

# Fetch and train on live Suno.com trending feed:
python -m src.trainer trending
```

Windows shortcut:
```cmd
train.bat "https://suno.com/song/<song-id>"
train.bat trending
```

#### Dataset Storage
- `corpus/suno_lyrics_corpus.jsonl` — Section-by-section scansion dataset with syllable counts and rhyme tags.
- `models/suno_song_catalog.json` — Indexed catalog of tracks with play counts, upvotes, and metadata.
- `models/suno_song_inference_model.json` — Compiled reference weights and style associations.

---

## Hardware Acceleration (Multi-GPU / SLI)

`src/hardware.py` inspects system topology at launch:
- Automatically detects single or dual NVIDIA GPUs (e.g., dual RTX 2080 in SLI / NVLink).
- Configures device distribution for training and inference when PyTorch CUDA is available.
- Check hardware status:
  ```bash
  python -c "import src.hardware; src.hardware.print_hardware_report()"
  ```

---

## Hugging Face Spaces Deployment

The repository includes a GitHub Actions workflow (`.github/workflows/deploy_huggingface.yml`) that deploys directly to the Hugging Face Space on push:

1. Open your repository on GitHub: **Settings** -> **Secrets and variables** -> **Actions**.
2. Add a repository secret named **`HFKEY`**.
3. Paste a Hugging Face User Access Token with **Write** permission (generated at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).
4. Every push to `main` (or manual trigger under the Actions tab) syncs the application to [wren11ws/suno_prompt_generator_v6](https://huggingface.co/spaces/wren11ws/suno_prompt_generator_v6).

---

## Web UI (Gradio)

Launch the local Gradio web interface:

```bash
python app.py
```

Opens at `http://127.0.0.1:7860`.

---

## License

Distributed under the [MIT License](LICENSE).
