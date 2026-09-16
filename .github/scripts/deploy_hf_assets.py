"""Deploy Suno Lyrics Scansion Corpus (Dataset) and Scansion-LM / Reference Model (Model) to Hugging Face Hub."""

from __future__ import annotations

import os
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
tags:
  - suno
  - music
  - lyrics
  - scansion
  - songwriting
language:
  - en
size_categories:
  - 10K<n<100K
---

# Suno AI Lyrics & Scansion Corpus (Suno Trends)

A curated dataset of **25,000+ scansion-formatted lyrical sections** and complete song sheets extracted and aligned for Suno AI Custom Mode prompting.

## Dataset Structure

- `train.jsonl` (`suno_lyrics_corpus.jsonl`): Contains prompt-completion pairs formatted for rhyme density, section continuation, and meter scansion.
- `catalog.json` (`suno_song_catalog.json`): Comprehensive catalog metadata for 9,075+ analyzed tracks, including play counts, upvotes, style tags, and duration.

## Usage with Hugging Face `datasets`

```python
from datasets import load_dataset

# Load full corpus
dataset = load_dataset("wren11ws/suno_trends")
print(dataset["train"][0])
```

## Schema

| Column | Type | Description |
|---|---|---|
| `prompt` | string | Section header prompt with brief, title, and target style |
| `text` | string | Full lyrical completion adhering to meter and rhyme constraints |
| `title` | string | Song title |
| `style` | string | Musical genre, tempo, and instrumental descriptors |
| `section` | string | Section type (e.g. `Verse`, `Chorus`, `Bridge`, `Outro`) |
| `kind` | string | `full_sheet` or `section_continuation` |
| `char_len` | int | Length in characters |

## License
MIT License.
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

    corpus_file = workspace / "corpus" / "suno_lyrics_corpus.jsonl"
    catalog_file = workspace / "models" / "suno_song_catalog.json"

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)
        # 1. Dataset Card
        (staging / "README.md").write_text(DATASET_README_TEMPLATE, encoding="utf-8")
        
        # 2. Files for standard datasets loader
        if corpus_file.exists():
            import shutil
            shutil.copy2(corpus_file, staging / "train.jsonl")
            shutil.copy2(corpus_file, staging / "suno_lyrics_corpus.jsonl")
            print(f"[+] Staged corpus: {corpus_file.stat().st_size // (1024*1024)} MB")
        
        if catalog_file.exists():
            import shutil
            shutil.copy2(catalog_file, staging / "catalog.json")
            print(f"[+] Staged catalog: {catalog_file.stat().st_size // 1024} KB")

        try:
            api.upload_folder(
                folder_path=str(staging),
                repo_id=repo_id,
                repo_type="dataset",
                commit_message="Update Suno lyrics corpus dataset from GitHub Actions",
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
    inf_model_file = workspace / "models" / "suno_song_inference_model.json"

    if not foundry_export.exists():
        print(f"[-] Foundry export folder not found at {foundry_export}", file=sys.stderr)
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)
        import shutil
        for item in foundry_export.iterdir():
            if item.is_file():
                shutil.copy2(item, staging / item.name)

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
