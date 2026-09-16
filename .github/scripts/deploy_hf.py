"""Deploy lightweight Hugging Face Space application using the secret HFKEY.

Resolves Space 1 GB storage limit by staging only runtime essentials:
- app.py, requirements.txt, README.md
- src/ package
- models/suno_song_inference_model.json (knowledge graph)
- models/scansion_lm/ tokenizer and config files (weights load dynamically from wren11ws/sunup)
- Purges raw corpora, catalogs, and duplicate dist/ build files from the Space repo.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from huggingface_hub import HfApi, create_repo

def main() -> int:
    token = os.environ.get("HFKEY") or os.environ.get("HF_TOKEN")
    if not token or not token.strip():
        print("[-] Error: Secret HFKEY is missing! Please configure it in your GitHub Repository Settings -> Secrets and variables -> Actions.", file=sys.stderr)
        return 1

    custom_space = os.environ.get("CUSTOM_SPACE", "").strip()
    repo_id = custom_space if custom_space else "wren11ws/suno_prompt_generator_v6"

    print("=" * 60)
    print("  HUGGING FACE SPACES DEPLOYMENT")
    print("=" * 60)
    print(f"Target Space Repo: {repo_id}")
    print("-" * 60)

    api = HfApi(token=token.strip())
    workspace = Path(__file__).resolve().parents[2]

    # 1. Ensure space exists
    try:
        api.repo_info(repo_id=repo_id, repo_type="space")
        print(f"[+] Space exists: https://huggingface.co/spaces/{repo_id}")
    except Exception:
        print(f"[*] Creating new Hugging Face Space: {repo_id} (Gradio SDK)...")
        try:
            create_repo(
                repo_id=repo_id,
                repo_type="space",
                space_sdk="gradio",
                private=False,
                token=token.strip(),
                exist_ok=True,
            )
            print(f"[+] Created Space: https://huggingface.co/spaces/{repo_id}")
        except Exception as exc:
            print(f"[!] Warning creating repo: {exc}")

    # 2. Stage only clean runtime files into temporary directory
    print("[*] Staging clean runtime bundle (resolving 1 GB Space limit)...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)

        # Core app files
        for fname in ["app.py", "requirements.txt", "README.md"]:
            src_file = workspace / fname
            if src_file.exists():
                shutil.copy2(src_file, staging / fname)
                print(f"    [+] Staged {fname}")

        # Python src package
        src_dir = workspace / "src"
        if src_dir.exists():
            shutil.copytree(
                src_dir,
                staging / "src",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
                dirs_exist_ok=True,
            )
            print("    [+] Staged src/ package")

        # Models: Inference knowledge graph (8.2 MB)
        inf_model = workspace / "models" / "suno_song_inference_model.json"
        if inf_model.exists():
            dest_models = staging / "models"
            dest_models.mkdir(parents=True, exist_ok=True)
            shutil.copy2(inf_model, dest_models / "suno_song_inference_model.json")
            size_mb = inf_model.stat().st_size / (1024 * 1024)
            print(f"    [+] Staged models/suno_song_inference_model.json ({size_mb:.2f} MB)")

        # Models: Scansion-LM configs & tokenizer (weights loaded on-demand from wren11ws/sunup)
        scansion_lm_src = workspace / "models" / "scansion_lm"
        if scansion_lm_src.exists():
            dest_slm = staging / "models" / "scansion_lm"
            dest_slm.mkdir(parents=True, exist_ok=True)
            for item in scansion_lm_src.iterdir():
                if item.is_file() and item.name != "model.safetensors":
                    shutil.copy2(item, dest_slm / item.name)
            print("    [+] Staged models/scansion_lm/ tokenizer & configs")

        # Calculate total bundle size
        total_bytes = sum(f.stat().st_size for f in staging.rglob("*") if f.is_file())
        print(f"[*] Total Space bundle size: {total_bytes / (1024 * 1024):.2f} MB (well within 1 GB limit)")

        # Patterns to delete from Space repository to free storage
        delete_patterns = [
            "models/suno_song_catalog.json",
            "models/scansion_lm/model.safetensors",
            "models/auto_train_processed.json",
            "foundry/*",
            "dist/*",
            "corpus/*",
            "server/*",
            "public/*",
            "nitro.json",
            "run.bat",
            "train.bat",
        ]

        print(f"[*] Uploading clean bundle and purging bloat from Space {repo_id}...")
        try:
            api.upload_folder(
                folder_path=str(staging),
                repo_id=repo_id,
                repo_type="space",
                delete_patterns=delete_patterns,
                commit_message="Clean deploy: purge training bloat and update Gradio v6 runtime",
            )
            print(f"[+] Successfully deployed to Hugging Face Spaces!")
            print(f"    URL: https://huggingface.co/spaces/{repo_id}")
            return 0
        except Exception as exc:
            print(f"[-] Failed to upload folder: {exc}", file=sys.stderr)
            return 1

if __name__ == "__main__":
    raise SystemExit(main())
