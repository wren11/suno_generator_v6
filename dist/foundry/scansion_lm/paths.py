from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RUNS = ROOT / "runs"
EXPORT = ROOT / "export"
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
