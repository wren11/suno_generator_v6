from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
for _cand in (ROOT.parent / "foundry" / "data", ROOT.parent / "dist" / "foundry" / "data", ROOT / "data"):
    if (_cand / "user_extracts.jsonl").exists() or (_cand / "seed_extracts.jsonl").exists():
        DATA = _cand
        break
RUNS = ROOT / "runs"
for _cand in (ROOT.parent / "foundry" / "runs", ROOT.parent / "dist" / "foundry" / "runs", ROOT / "runs"):
    if _cand.exists():
        RUNS = _cand
        break
EXPORT = ROOT / "export"
for _cand in (ROOT / "export", ROOT.parent / "foundry" / "export", ROOT.parent / "dist" / "foundry" / "export"):
    if (_cand / "model.safetensors").exists() and (_cand / "config.json").exists():
        EXPORT = _cand
        break
USER_EXTRACTS = DATA / "user_extracts.jsonl"
SEED_EXTRACTS = DATA / "seed_extracts.jsonl"
TRENDING_JSON = DATA / "suno-trending.json"
HITS_JSON = DATA / "hits.json"
CORPUS_JSONL = DATA / "corpus.jsonl"
TOKENIZER_DIR = DATA / "tokenizer"
METRICS = RUNS / "metrics.jsonl"
STATUS = RUNS / "status.json"
TRAIN_LOG = RUNS / "train.log"
MODEL_CARD = ROOT / "README.md"
LICENSE = ROOT / "LICENSE"
FOUNDRY_HOST = "127.0.0.1"
FOUNDRY_PORT = 8099
MAX_LEN = 512
VOCAB_SIZE = 8192

for _p in (DATA, RUNS, EXPORT, TOKENIZER_DIR):
    _p.mkdir(parents=True, exist_ok=True)
