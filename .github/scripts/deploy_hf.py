"""Deploy repository and Hugging Face Space using the secret HFKEY."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from huggingface_hub import HfApi, create_repo

def main() -> int:
    token = os.environ.get("HFKEY") or os.environ.get("HF_TOKEN")
    if not token or not token.strip():
        print("[-] Error: Secret HFKEY is missing! Please configure it in your GitHub Repository Settings -> Secrets and variables -> Actions.", file=sys.stderr)
        return 1

    custom_space = os.environ.get("CUSTOM_SPACE", "").strip()
    github_repo = os.environ.get("GITHUB_REPO", "wren11/suno_generator_v6").strip()

    # Determine space repo id
    if custom_space:
        repo_id = custom_space
    elif "/" in github_repo:
        user = github_repo.split("/")[0]
        repo_id = f"{user}/suno-generator-v6"
    else:
        repo_id = "wren11/suno-generator-v6"

    print("=" * 60)
    print("  HUGGING FACE SPACES DEPLOYMENT")
    print("=" * 60)
    print(f"Target Space Repo: {repo_id}")
    print("-" * 60)

    api = HfApi(token=token.strip())

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

    # 2. Upload Space contents
    workspace = Path(__file__).resolve().parents[2]
    print(f"[*] Uploading files from {workspace} to Space {repo_id}...")

    # Upload all essentials while ignoring git and caches
    ignore_patterns = [
        ".git/*",
        ".github/*",
        "*.pyc",
        "__pycache__/*",
        ".pytest_cache/*",
        "dist/output/*",
        "output/*",
        "runs/*",
        ".system_generated/*",
    ]

    try:
        future = api.upload_folder(
            folder_path=str(workspace),
            repo_id=repo_id,
            repo_type="space",
            ignore_patterns=ignore_patterns,
            commit_message="Automated release from GitHub Actions (HFKEY)",
        )
        print(f"[+] Successfully deployed to Hugging Face Spaces!")
        print(f"    URL: https://huggingface.co/spaces/{repo_id}")
        return 0
    except Exception as exc:
        print(f"[-] Failed to upload folder: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
