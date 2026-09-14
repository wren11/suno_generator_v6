"""Hugging Face Space Deployment tool for Suno Generator."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def deploy_to_hf_space(
    repo_id: str,
    *,
    token: str | None = None,
    space_sdk: str = "gradio",
    private: bool = False,
) -> str:
    from huggingface_hub import HfApi, login

    hf_token = token or os.environ.get("HF_TOKEN") or ""
    if not hf_token:
        print("\n[?] Hugging Face API Token required for deployment.")
        print("    Get your free write token at: https://huggingface.co/settings/tokens")
        hf_token = input("Enter Hugging Face Token (hf_...): ").strip()

    if not hf_token:
        raise ValueError("Deployment cancelled: Hugging Face API token is required.")

    api = HfApi(token=hf_token)
    user_info = api.whoami()
    username = user_info.get("name", "")
    print(f"[+] Authenticated as Hugging Face user: {username}")

    if "/" not in repo_id:
        repo_id = f"{username}/{repo_id}"

    print(f"[*] Creating or updating Hugging Face Space: '{repo_id}' (SDK: {space_sdk}) ...")
    space_url = api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk=space_sdk,
        private=private,
        exist_ok=True,
    )
    print(f"[+] Space repository ready: {repo_id}")

    root_dir = Path(__file__).resolve().parent.parent

    # Files to upload
    files_to_upload = [
        ("app.py", "app.py"),
        ("requirements.txt", "requirements.txt"),
        ("README.md", "README.md"),
    ]

    # Model file
    model_src = root_dir / "models" / "suno_song_inference_model.json"
    if not model_src.exists():
        model_src = root_dir / "dist" / "models" / "suno_song_inference_model.json"

    if model_src.exists():
        files_to_upload.append((str(model_src), "models/suno_song_inference_model.json"))

    print(f"[*] Uploading root files to Space '{repo_id}'...")
    for local_rel, remote_path in files_to_upload:
        p = root_dir / local_rel if not Path(local_rel).is_absolute() else Path(local_rel)
        if p.exists():
            print(f"  -> Uploading {remote_path} ({p.stat().st_size // 1024} KB)...")
            api.upload_file(
                path_or_fileobj=str(p),
                path_in_repo=remote_path,
                repo_id=repo_id,
                repo_type="space",
            )

    # Upload src/ folder
    src_dir = root_dir / "src"
    if src_dir.exists():
        print(f"[*] Uploading 'src/' package to Space '{repo_id}'...")
        api.upload_folder(
            folder_path=str(src_dir),
            path_in_repo="src",
            repo_id=repo_id,
            repo_type="space",
        )

    live_url = f"https://huggingface.co/spaces/{repo_id}"
    print("\n" + "=" * 65)
    print("  HUGGING FACE SPACE DEPLOYMENT SUCCESSFUL!")
    print("=" * 65)
    print(f"  Live Space URL: {live_url}")
    print("  Your space is now building and will be live in 1-2 minutes.")
    print("=" * 65 + "\n")
    return live_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Suno Generator as a public Hugging Face Space.")
    parser.add_argument("repo_id", nargs="?", default="", help="Space repo id, e.g. 'username/suno-generator'")
    parser.add_argument("--token", default=None, help="Hugging Face API token (or HF_TOKEN env var)")
    parser.add_argument("--private", action="store_true", help="Set space visibility to private")
    args = parser.parse_args()

    target_repo = args.repo_id.strip()
    if not target_repo:
        print("=" * 60)
        print("  DEPLOY SUNO GENERATOR TO HUGGING FACE SPACES")
        print("=" * 60)
        default_name = "suno-song-generator"
        target_repo = input(f"Enter Space name or repo ID [default: {default_name}]: ").strip() or default_name

    deploy_to_hf_space(target_repo, token=args.token, private=args.private)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
