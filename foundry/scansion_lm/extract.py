"""Extract meter, rhyme, and section DNA from lyric text — the guide's coding layer."""

from __future__ import annotations

import re
from collections import Counter

FUNCTION = {
    "a", "an", "the", "and", "or", "but", "if", "to", "of", "in", "on", "at",
    "for", "from", "with", "by", "as", "is", "are", "was", "were", "be", "been",
    "am", "i", "you", "he", "she", "it", "we", "they", "my", "your", "his",
    "her", "our", "their", "me", "him", "us", "them", "this", "that", "these",
    "those", "not", "no", "so", "too", "just", "than", "then",
}

VOWELS = re.compile(r"[aeiouy]+", re.I)
WORD = re.compile(r"[a-zA-Z']+")

FOOT_TABLE = [
    ("spondee", [1, 1]),
    ("iamb", [0, 1]),
    ("trochee", [1, 0]),
    ("anapest", [0, 0, 1]),
    ("dactyl", [1, 0, 0]),
    ("amphibrach", [0, 1, 0]),
    ("pyrrhic", [0, 0]),
]


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    parts = VOWELS.findall(w)
    n = len(parts)
    if w.endswith("e") and n > 1 and not w.endswith("le"):
        n -= 1
    return max(1, n)


def stress_word(word: str) -> list[int]:
    n = syllables(word)
    if n <= 0:
        return []
    if word.lower() in FUNCTION:
        return [0] * n
    if n == 1:
        return [1]
    if n == 2:
        return [1, 0]
    return [1] + [0] * (n - 1)


def line_stress(line: str) -> list[int]:
    bits: list[int] = []
    for w in WORD.findall(line):
        bits.extend(stress_word(w))
    return bits


def classify_foot(stress: list[int]) -> str:
    if not stress:
        return "pyrrhic"
    best, best_n = "free", -1
    for name, pat in FOOT_TABLE:
        hits = 0
        i = 0
        while i + len(pat) <= len(stress):
            if stress[i : i + len(pat)] == pat:
                hits += 1
                i += len(pat)
            else:
                i += 1
        if hits > best_n:
            best, best_n = name, hits
    return best


def rhyme_key(line: str) -> str:
    words = WORD.findall(line.lower())
    if not words:
        return ""
    w = re.sub(r"[^a-z]", "", words[-1])
    m = list(VOWELS.finditer(w))
    if not m:
        return w[-2:] if len(w) >= 2 else w
    start = m[-1].start()
    return w[start:]


def rhyme_schema(lines: list[str]) -> str:
    keys = [rhyme_key(l) for l in lines if l.strip() and not l.strip().startswith("[")]
    if not keys:
        return ""
    letter: dict[str, str] = {}
    out = []
    alpha = "ABCDEFGH"
    for k in keys:
        if k not in letter:
            letter[k] = alpha[len(letter) % len(alpha)]
        out.append(letter[k])
    return "".join(out)


def split_sections(text: str) -> list[dict]:
    sections: list[dict] = []
    current = "Body"
    buf: list[str] = []
    tag = re.compile(r"^\[([^\]]+)\]\s*$")
    for raw in text.splitlines():
        line = raw.rstrip()
        m = tag.match(line.strip())
        if m:
            if buf:
                sections.append({"name": current, "lines": buf})
                buf = []
            current = m.group(1)
            continue
        if line.strip():
            buf.append(line)
    if buf:
        sections.append({"name": current, "lines": buf})
    return sections


def punctuation_profile(text: str) -> dict[str, int]:
    return {
        "periods": text.count("."),
        "commas": text.count(","),
        "questions": text.count("?"),
        "exclaims": text.count("!"),
        "parens": text.count("("),
        "blank_lines": len(re.findall(r"\n\s*\n", text)),
    }


def extract_song(text: str, title: str = "", source: str = "user") -> dict:
    sections = split_sections(text)
    lyric_lines = [ln for s in sections for ln in s["lines"] if not ln.startswith("[")]
    meters = []
    for s in sections:
        feet = [classify_foot(line_stress(ln)) for ln in s["lines"]]
        meters.append(
            {
                "section": s["name"],
                "lines": len(s["lines"]),
                "dominant_foot": Counter(feet).most_common(1)[0][0] if feet else "free",
                "feet": feet[:12],
            }
        )
    masculine = 0
    feminine = 0
    for ln in lyric_lines:
        st = line_stress(ln)
        if not st:
            continue
        if st[-1] == 1:
            masculine += 1
        else:
            feminine += 1
    return {
        "title": title or "Untitled extract",
        "source": source,
        "text": text.strip(),
        "sections": [s["section"] for s in meters],
        "meter_map": meters,
        "rhyme_schema": rhyme_schema(lyric_lines),
        "masculine_endings": masculine,
        "feminine_endings": feminine,
        "energy": "aggressive" if masculine > feminine + 2 else "passive" if feminine > masculine + 2 else "balanced",
        "punctuation": punctuation_profile(text),
        "line_count": len(lyric_lines),
        "sung": lyric_lines,
    }
