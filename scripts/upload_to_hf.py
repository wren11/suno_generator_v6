"""Upload Suno models, datasets, and spaces to Hugging Face Hub.

Usage:
  python scripts/upload_to_hf.py --token <HFKEY> [--target all|model|dataset|space]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_MODEL_REPO = "wren11ws/sunup"
DEFAULT_DATASET_REPO = "wren11ws/suno_trends"
DEFAULT_SPACE_REPO = "wren11ws/suno_prompt_generator_v6"


def upload_model(api, repo_id: str, workspace: Path) -> bool:
    print("\n" + "=" * 65)
    print(f"  [1/3] UPLOADING NEURAL MODEL TO HUGGING FACE: {repo_id}")
    print("=" * 65)
    
    from huggingface_hub import create_repo
    try:
        create_repo(repo_id=repo_id, repo_type="model", private=False, exist_ok=True)
        print(f"[+] Verified model repo: https://huggingface.co/{repo_id}")
    except Exception as ex:
        print(f"[!] Info creating repo: {ex}")

    foundry_export = workspace / "foundry" / "export"
    scansion_lm_dir = workspace / "models" / "scansion_lm"
    src_dir = foundry_export if (foundry_export / "model.safetensors").exists() else scansion_lm_dir

    if not (src_dir / "model.safetensors").exists():
        print(f"[-] Error: model.safetensors not found in {src_dir}!", file=sys.stderr)
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)
        files = list(src_dir.glob("*"))
        print(f"[*] Staging {len(files)} model files from {src_dir} ...")
        for f in files:
            if f.is_file():
                shutil.copy2(f, staging / f.name)
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"    - {f.name} ({size_mb:.2f} MB)")

        inf_model = workspace / "models" / "suno_song_inference_model.json"
        if inf_model.exists():
            shutil.copy2(inf_model, staging / "suno_song_inference_model.json")
            print(f"    - suno_song_inference_model.json ({inf_model.stat().st_size / (1024 * 1024):.2f} MB)")

        print(f"[*] Uploading model folder to https://huggingface.co/{repo_id} ...")
        try:
            api.upload_folder(
                folder_path=str(staging),
                repo_id=repo_id,
                repo_type="model",
                commit_message="Update Scansion-LM weights & knowledge graph from local training",
            )
            print(f"[+] Model successfully published to: https://huggingface.co/{repo_id}")
            return True
        except Exception as exc:
            print(f"[-] Error uploading model: {exc}", file=sys.stderr)
            return False


def upload_dataset(api, repo_id: str, workspace: Path) -> bool:
    print("\n" + "=" * 65)
    print(f"  [2/3] UPLOADING DATASET & CATALOG TO HUGGING FACE: {repo_id}")
    print("=" * 65)

    from huggingface_hub import create_repo
    try:
        create_repo(repo_id=repo_id, repo_type="dataset", private=False, exist_ok=True)
        print(f"[+] Verified dataset repo: https://huggingface.co/datasets/{repo_id}")
    except Exception as ex:
        print(f"[!] Info creating dataset repo: {ex}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)
        
        # 1. Knowledge graph
        inf_file = workspace / "models" / "suno_song_inference_model.json"
        if inf_file.exists():
            shutil.copy2(inf_file, staging / "reference_knowledge_graph.json")
            print(f"    [+] Staged reference_knowledge_graph.json ({inf_file.stat().st_size / (1024 * 1024):.2f} MB)")

        # 2. Extracts
        user_ext = workspace / "foundry" / "data" / "user_extracts.jsonl"
        if user_ext.exists():
            shutil.copy2(user_ext, staging / "user_lyric_extracts.jsonl")
            print(f"    [+] Staged user_lyric_extracts.jsonl ({user_ext.stat().st_size / (1024 * 1024):.2f} MB)")

        # 3. Training corpus
        corpus_file = workspace / "foundry" / "data" / "corpus.jsonl"
        if corpus_file.exists():
            shutil.copy2(corpus_file, staging / "scansion_lm_training_corpus.jsonl")
            print(f"    [+] Staged scansion_lm_training_corpus.jsonl ({corpus_file.stat().st_size / (1024 * 1024):.2f} MB)")

        # 4. 10,000 Curated Master Songs Dataset
        curated_10k = workspace / "models" / "suno_10000_songs_curated.jsonl"
        if curated_10k.exists():
            shutil.copy2(curated_10k, staging / "suno_10000_songs_curated.jsonl")
            print(f"    [+] Staged suno_10000_songs_curated.jsonl ({curated_10k.stat().st_size / (1024 * 1024):.2f} MB)")

        # 5. Catalog
        cat_file = workspace / "models" / "suno_song_catalog.json"
        if cat_file.exists():
            shutil.copy2(cat_file, staging / "catalog.json")
            print(f"    [+] Staged catalog.json ({cat_file.stat().st_size / (1024 * 1024):.2f} MB)")

        print(f"[*] Uploading dataset to https://huggingface.co/datasets/{repo_id} ...")
        try:
            api.upload_folder(
                folder_path=str(staging),
                repo_id=repo_id,
                repo_type="dataset",
                commit_message="Update Suno catalog, scansion extracts, and knowledge graph",
            )
            print(f"[+] Dataset successfully published to: https://huggingface.co/datasets/{repo_id}")
            return True
        except Exception as exc:
            print(f"[-] Error uploading dataset: {exc}", file=sys.stderr)
            return False


def upload_space(api, repo_id: str, workspace: Path) -> bool:
    print("\n" + "=" * 65)
    print(f"  [3/3] UPLOADING APP TO HUGGING FACE SPACES: {repo_id}")
    print("=" * 65)

    from huggingface_hub import create_repo
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="gradio",
            private=False,
            exist_ok=True,
        )
        print(f"[+] Verified Space: https://huggingface.co/spaces/{repo_id}")
    except Exception as ex:
        print(f"[!] Info creating Space: {ex}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging = Path(tmp_dir)

        # Core app files
        for fname in ["app.py", "requirements.txt", "README.md", "chat_app.py"]:
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

        # Models: Inference knowledge graph
        inf_model = workspace / "models" / "suno_song_inference_model.json"
        if inf_model.exists():
            dest_models = staging / "models"
            dest_models.mkdir(parents=True, exist_ok=True)
            shutil.copy2(inf_model, dest_models / "suno_song_inference_model.json")
            print(f"    [+] Staged models/suno_song_inference_model.json ({inf_model.stat().st_size / (1024 * 1024):.2f} MB)")

        # Models: Tokenizer & configs (No 327MB safetensors! Space loads weights from wren11ws/sunup)
        scansion_lm_src = workspace / "models" / "scansion_lm"
        if scansion_lm_src.exists():
            dest_slm = staging / "models" / "scansion_lm"
            dest_slm.mkdir(parents=True, exist_ok=True)
            for item in scansion_lm_src.iterdir():
                if item.is_file() and item.suffix != ".safetensors" and item.suffix != ".bin":
                    shutil.copy2(item, dest_slm / item.name)
            print("    [+] Staged models/scansion_lm/ tokenizer & configs (lightweight)")

        print(f"[*] Uploading clean runtime bundle to https://huggingface.co/spaces/{repo_id} ...")
        try:
            api.upload_folder(
                folder_path=str(staging),
                repo_id=repo_id,
                repo_type="space",
                commit_message="Deploy updated SunoGPT Studio to Hugging Face Spaces",
            )
            print(f"[+] Space successfully deployed: https://huggingface.co/spaces/{repo_id}")
            return True
        except Exception as exc:
            print(f"[-] Error uploading Space: {exc}", file=sys.stderr)
            return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload Suno models, datasets, and spaces to Hugging Face Hub")
    parser.add_argument("--token", help="Hugging Face API Token (HFKEY)")
    parser.add_argument("--target", choices=["all", "model", "dataset", "space"], default="all", help="What to upload")
    parser.add_argument("--model-repo", default=DEFAULT_MODEL_REPO, help="Model repo id")
    parser.add_argument("--dataset-repo", default=DEFAULT_DATASET_REPO, help="Dataset repo id")
    parser.add_argument("--space-repo", default=DEFAULT_SPACE_REPO, help="Space repo id")
    args = parser.parse_args()

    token = args.token or os.environ.get("HFKEY") or os.environ.get("HF_TOKEN")
    if not token or not token.strip():
        print("[-] Error: Hugging Face Token (HFKEY) is required!", file=sys.stderr)
        print("    Pass via: python scripts/upload_to_hf.py --token <YOUR_HFKEY>", file=sys.stderr)
        print("    Or set:   $env:HFKEY = '<YOUR_HFKEY>'", file=sys.stderr)
        return 1

    from huggingface_hub import HfApi
    try:
        api = HfApi(token=token.strip())
        user_info = api.whoami()
        print(f"[+] Authenticated successfully as: {user_info.get('name', 'User')}")
    except Exception as ex:
        print(f"[-] Authentication failed with provided token: {ex}", file=sys.stderr)
        return 1

    workspace = Path(__file__).resolve().parent.parent
    ok = True

    if args.target in ("all", "model"):
        if not upload_model(api, args.model_repo, workspace):
            ok = False

    if args.target in ("all", "dataset"):
        if not upload_dataset(api, args.dataset_repo, workspace):
            ok = False

    if args.target in ("all", "space"):
        if not upload_space(api, args.space_repo, workspace):
            ok = False

    print("\n" + "=" * 65)
    if ok:
        print("  ALL REQUESTED ASSETS SUCCESSFULLY PUBLISHED TO HUGGING FACE!")
    else:
        print("  COMPLETED WITH SOME WARNINGS / ERRORS.")
    print("=" * 65)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
