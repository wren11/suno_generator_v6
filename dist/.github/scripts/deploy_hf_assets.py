"""Deploy Suno Lyrics & Scansion Corpus (Dataset) and Scansion-LM / Reference Model (Model) to Hugging Face Hub."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from huggingface_hub import HfApi, create_repo

DEFAULT_DATASET_REPO = "wren11ws/suno_trends"
DEFAULT_MODEL_REPO = "wren11ws/sunup"

DATASET_README_TEMPLATE = """---
license: mit
task_categories:
  - text-generation
  - feature-extraction
tags:
  - suno
  - music
  - lyrics
  - scansion
  - songwriting
  - prompt-engineering
language:
  - en
size_categories:
  - 10K<n<100K
pretty_name: "Suno AI Trends & Scansion Lyrics Dataset"
dataset_info:
  features:
    - name: prompt
      dtype: string
    - name: text
      dtype: string
    - name: title
      dtype: string
    - name: style
      dtype: string
    - name: section
      dtype: string
    - name: kind
      dtype: string
    - name: char_len
      dtype: int64
  splits:
    - name: train
      num_bytes: 81687615
      num_examples: 65284
---

# Suno AI Trends & Lyrics Scansion Dataset (`{dataset_repo}`)

A curated dataset and ML training corpus containing **65,284 scansion-formatted lyrical sections**, complete song sheets, and structural metadata aligned for Suno AI Custom Mode prompting, rhyme density modeling, and musical meter analysis.

## Dataset Structure & Files

This repository contains the complete training, scansion, and catalog data powering the [Suno Prompt Generator v6](https://huggingface.co/spaces/wren11ws/suno_prompt_generator_v6) and [Scansion-LM](https://huggingface.co/wren11ws/sunup):

| File | Size | Description |
|---|---|---|
| `train.jsonl` | ~82 MB | Default Hugging Face `train` split: 65,284 prompt-completion pairs formatted for section continuation, rhyme density, and meter scansion. |
| `suno_lyrics_corpus.jsonl` | ~82 MB | Full lyrical corpus with titles, styles, sections, and character lengths. |
| `suno_lyrics_corpus.stats.json` | <1 KB | High-level statistics on vocabulary size, section distribution, and token counts. |
| `catalog.json` / `suno_song_catalog.json` | ~192 MB | 16,082 cataloged top Suno tracks with play counts, upvotes, style descriptors, durations, and metadata. |
| `reference_knowledge_graph.json` | ~8.2 MB | Genre transition probabilities, tempo clustering, and scansion inference graph rules. |
| `scansion_lm_training_corpus.jsonl` | ~328 KB | DistilGPT2 fine-tuning training corpus with `<|endoftext|>` tokens and section headers. |
| `user_lyric_extracts.jsonl` | ~940 KB | Scansion extracts annotated with foot types (iambic, trochaic, spondaic), line counts, rhyme schemes, and masculine/feminine endings. |
| `seed_scansion_extracts.jsonl` | ~77 KB | Curated golden scansion seeds spanning folk, desert rock, synthwave, and cinematic genres. |
| `suno_trending_snapshots.json` | ~118 KB | Trending feed snapshots capturing ranking positions, play velocity, and community engagement. |
| `auto_train_processed.json` | ~2 MB | Crawl statuses and provenance mapping for processed track IDs. |
| `tokenizer/` | Directory | Custom BPE tokenizer configuration, vocabulary mappings, and special tokens. |

## Quickstart: Loading with Python

### 1. Load the Core Lyrics Split (`datasets`)
```python
from datasets import load_dataset

# Load default train split
dataset = load_dataset("{dataset_repo}")
print(dataset["train"][0])
```

Sample record:
```json
{{
  "prompt": "Title: Heat Line\\nIdea: A man scraping survival out of desert heat\\nVerse:\\n",
  "text": "He scrapes at the basin for a mouthful of shade\\nThe highway keeps humming a colorless note\\nDust writes his name on the back of his throat",
  "title": "Heat Line",
  "style": "desert rock, gritty slide guitar, 120 bpm, andante",
  "section": "Verse",
  "kind": "section_continuation",
  "char_len": 182
}}
```

### 2. Loading Scansion Extracts or Catalogs directly
```python
from huggingface_hub import hf_hub_download
import json

# Download and inspect song catalog
catalog_path = hf_hub_download(repo_id="{dataset_repo}", repo_type="dataset", filename="catalog.json")
with open(catalog_path, "r", encoding="utf-8") as f:
    catalog = json.load(f)
print(f"Loaded {{len(catalog)}} cataloged Suno songs")

# Download scansion extracts with meter maps
extracts_path = hf_hub_download(repo_id="{dataset_repo}", repo_type="dataset", filename="user_lyric_extracts.jsonl")
with open(extracts_path, "r", encoding="utf-8") as f:
    for line in f:
        sample = json.loads(line)
        print("Song:", sample["title"], "| Meter Map:", sample.get("meter_map"))
        break
```

## Schema Reference

### `train.jsonl` / `suno_lyrics_corpus.jsonl`
- `prompt` (`str`): Prompt header including song title, concept idea, and section tag.
- `text` (`str`): Target lyrical continuation adhering to meter, scansion, and rhyme scheme.
- `title` (`str`): Song title.
- `style` (`str`): Music genre, instrumentation, tempo, and Italian feel descriptors.
- `section` (`str`): Section type (`Verse`, `Chorus`, `Bridge`, `Outro`, `Intro`).
- `kind` (`str`): `section_continuation` or `full_sheet`.
- `char_len` (`int`): Character length of completion.

### `user_lyric_extracts.jsonl` & `seed_scansion_extracts.jsonl`
- `title` (`str`): Song title.
- `source` (`str`): Extract source / theme.
- `text` (`str`): Complete song sheet with metatag sandwich (`[Start]`, `[Verse]`, `[Chorus]`, etc.).
- `meter_map` (`list[dict]`): Foot-by-foot poetic scansion per line (`iamb`, `trochee`, `spondee`, `dactyl`, `anapest`).
- `rhyme_schema` (`str`): Rhyme structure sequence (e.g. `AABACCDDEEFG`).
- `masculine_endings` (`int`): Count of stressed ending syllables.
- `feminine_endings` (`int`): Count of unstressed ending syllables.
- `energy` (`str`): Delivery dynamic (`aggressive`, `contemplative`, etc.).
- `line_count` (`int`): Total line count.
- `sung` (`list[str]`): List of pure sung lyric lines stripped of bracket directives.
- `dna` (`str`): Structural songwriting analysis notes.

## Connected Ecosystem
- **Hugging Face Space**: [wren11ws/suno_prompt_generator_v6](https://huggingface.co/spaces/wren11ws/suno_prompt_generator_v6)
- **Hugging Face Model**: [wren11ws/sunup](https://huggingface.co/wren11ws/sunup)
- **GitHub Repository**: [wren11ws/suno_generator_v6](https://github.com/wren11ws/suno_generator_v6)

## License
MIT License. Free for research, musicology, and AI songwriting model development.
"""


def deploy_dataset(api: HfApi, repo_id: str, workspace: Path) -> bool:
    print("\n" + "=" * 60)
    print(f"  DEPLOYING DATASET: {repo_id}")
    print("=" * 60)
    try:
        create_repo(repo_id=repo_id, repo_type="dataset", private=False, exist_ok=True)
        print(f"[+] Verified / Created dataset repo: https://huggingface.co/datasets/{repo_id}")
    except Exception as exc:
        print(f"[!] Warning on create_repo: {exc}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)
        # 1. Dataset Card
        readme_content = DATASET_README_TEMPLATE.format(dataset_repo=repo_id)
        (staging / "README.md").write_text(readme_content, encoding="utf-8")

        # 2. Files for standard datasets loader & ML training
        file_mappings = [
            # (source, [destinations in dataset repo])
            (workspace / "corpus" / "suno_lyrics_corpus.jsonl", ["train.jsonl", "suno_lyrics_corpus.jsonl"]),
            (workspace / "corpus" / "suno_lyrics_corpus.stats.json", ["suno_lyrics_corpus.stats.json"]),
            (workspace / "models" / "suno_song_catalog.json", ["catalog.json", "suno_song_catalog.json"]),
            (workspace / "models" / "suno_song_inference_model.json", ["reference_knowledge_graph.json", "suno_song_inference_model.json"]),
            (workspace / "models" / "auto_train_processed.json", ["auto_train_processed.json"]),
            (workspace / "foundry" / "data" / "corpus.jsonl", ["scansion_lm_training_corpus.jsonl"]),
            (workspace / "foundry" / "data" / "user_extracts.jsonl", ["user_lyric_extracts.jsonl"]),
            (workspace / "foundry" / "data" / "seed_extracts.jsonl", ["seed_scansion_extracts.jsonl"]),
            (workspace / "foundry" / "data" / "suno-trending.json", ["suno_trending_snapshots.json"]),
        ]

        staged_count = 0
        for src, dest_names in file_mappings:
            if src.exists():
                for dname in dest_names:
                    dest = staging / dname
                    shutil.copy2(src, dest)
                    size_mb = src.stat().st_size / (1024 * 1024)
                    print(f"[+] Staged {dname} ({size_mb:.2f} MB)")
                    staged_count += 1
            else:
                print(f"[-] Source not found: {src}")

        # Stage tokenizer directory if present
        tokenizer_dir = workspace / "foundry" / "data" / "tokenizer"
        if tokenizer_dir.exists() and tokenizer_dir.is_dir():
            dest_tok = staging / "tokenizer"
            shutil.copytree(tokenizer_dir, dest_tok, dirs_exist_ok=True)
            print(f"[+] Staged tokenizer directory ({len(list(tokenizer_dir.glob('*')))} files)")
            staged_count += 1

        print(f"[*] Total dataset items staged: {staged_count}. Uploading to Hugging Face...")
        try:
            api.upload_folder(
                folder_path=str(staging),
                repo_id=repo_id,
                repo_type="dataset",
                commit_message="Update Suno lyrics, trends and scansion ML dataset from GitHub Actions",
            )
            print(f"[+] Successfully deployed dataset: https://huggingface.co/datasets/{repo_id}")
            return True
        except Exception as exc:
            print(f"[-] Failed uploading dataset: {exc}", file=sys.stderr)
            return False


def deploy_model(api: HfApi, repo_id: str, workspace: Path) -> bool:
    print("\n" + "=" * 60)
    print(f"  DEPLOYING MODEL: {repo_id}")
    print("=" * 60)
    try:
        create_repo(repo_id=repo_id, repo_type="model", private=False, exist_ok=True)
        print(f"[+] Verified / Created model repo: https://huggingface.co/models/{repo_id}")
    except Exception as exc:
        print(f"[!] Warning on create_repo: {exc}")

    foundry_export = workspace / "foundry" / "export"
    scansion_lm_dir = workspace / "models" / "scansion_lm"
    inf_model_file = workspace / "models" / "suno_song_inference_model.json"

    export_dir = foundry_export if foundry_export.exists() else scansion_lm_dir
    if not export_dir.exists():
        print(f"[-] Model export folder not found at {foundry_export} or {scansion_lm_dir}", file=sys.stderr)
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)
        for item in export_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, staging / item.name)
                print(f"[+] Staged model file: {item.name}")

        if inf_model_file.exists():
            shutil.copy2(inf_model_file, staging / "suno_song_inference_model.json")
            print(f"[+] Bundled reference model weights graph ({inf_model_file.stat().st_size // 1024} KB)")

        try:
            api.upload_folder(
                folder_path=str(staging),
                repo_id=repo_id,
                repo_type="model",
                commit_message="Update Scansion-LM & Reference Model from GitHub Actions",
            )
            print(f"[+] Successfully deployed model: https://huggingface.co/models/{repo_id}")
            return True
        except Exception as exc:
            print(f"[-] Failed uploading model: {exc}", file=sys.stderr)
            return False


def main() -> int:
    token = os.environ.get("HFKEY") or os.environ.get("HF_TOKEN")
    if not token or not token.strip():
        print("[-] Error: Secret HFKEY is missing! Please configure it in your GitHub Repository Secrets.", file=sys.stderr)
        return 1

    api = HfApi(token=token.strip())
    workspace = Path(__file__).resolve().parents[2]

    target = os.environ.get("DEPLOY_TARGET", "all").lower().strip()
    dataset_repo = os.environ.get("DATASET_REPO", DEFAULT_DATASET_REPO).strip()
    model_repo = os.environ.get("MODEL_REPO", DEFAULT_MODEL_REPO).strip()

    ok = True
    if target in ("all", "dataset"):
        if not deploy_dataset(api, dataset_repo, workspace):
            ok = False

    if target in ("all", "model"):
        if not deploy_model(api, model_repo, workspace):
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
