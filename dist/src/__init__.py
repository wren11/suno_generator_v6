"""Suno Generator - AI Songwriting Reference Model & REPL Harness."""

__version__ = "1.0.0"

from src.catalog import SongCatalogStore, SongRecord, song_id_from_url
from src.features import compute_lyric_stats, derive_song_features
from src.inference import SongwritingReferenceModel
from src.keywords import ENGLISH_SEED_KEYWORDS, KeywordStyleAnalytics, tokenize_creative_text
from src.llm import ScansionLLM, generate_suno_v6_payload

__all__ = [
    "SongCatalogStore",
    "SongRecord",
    "song_id_from_url",
    "compute_lyric_stats",
    "derive_song_features",
    "SongwritingReferenceModel",
    "ENGLISH_SEED_KEYWORDS",
    "KeywordStyleAnalytics",
    "tokenize_creative_text",
    "ScansionLLM",
    "generate_suno_v6_payload",
]
