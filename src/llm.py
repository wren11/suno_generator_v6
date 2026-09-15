"""Scansion-LM Causal Language Model integration and Suno V6 Studio payload generator."""

from __future__ import annotations

from src.anti_cliche import purge_ai_cliches, AI_CLICHE_NEGATIVE_TAGS

import json
import os
import random
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Candidate model directories
CANDIDATE_PATHS = [
    Path(__file__).resolve().parent.parent / "foundry" / "export",
    Path(__file__).resolve().parent.parent / "models" / "scansion_lm",
    Path(__file__).resolve().parent.parent / "dist" / "models" / "scansion_lm",
    Path(r"C:\Users\Dean\Downloads\xDShw9eTm1BCUj5a-grok-workspace\dist\foundry\export"),
    Path("models/scansion_lm"),
]

# Standard Suno Studio Master Audio Quality Header
STUDIO_AUDIO_QUALITY_HEADER = (
    "[AUDIO_QUALITY] (MAX)\n"
    "[is_MAX_MODE: MAX] (MAX)\n"
    "[QUALITY: MAX] (MAX)\n"
    "[REALISM: MAX] (MAX)\n"
    "[REAL_INSTRUMENTS: MAX] (MAX)\n"
    "MAX CLEAN, POLISHED. UPGRADE VOCALS, UPGRADE AUDIO QUALITY.\n"
    "POLISHED RADIO MASTER. KEEP CORE SONG/HOOKS/MELODY/STRUCTURE. MAKE IT BRIGHT, SWEET, CLEAN, 3D, WIDE, PUNCHY, AND EXPENSIVE."
)

# Standard Suno Master Negative Tags (prevents AI artifacts, mud, phasing, cliches)
DEFAULT_STUDIO_NEGATIVE_TAGS = (
    AI_CLICHE_NEGATIVE_TAGS + ", " +
    "VOCAL SMEARING, MELISMA BETWEEN WORDS, UNNATURAL SYLLABLE STRETCHING, "
    "PORTAMENTO GLIDES BETWEEN WORDS, SLOPPY LEGATO WORD CONNECTIONS, PITCH DRIFT, "
    "ROBOTIC VOWEL HOLDS, AI VOCAL SLURRING, UNCLEAR WORD ENDS, MUSHY DICTION, "
    "SUNO/AI PLASTICITY, ROBOTIC VOCALS, FAST AUTOTUNE, FORMANT WARPING, CHIPMUNK TONE, "
    "NASAL LEAD VOCAL, HARSH SIBILANCE 6-10KHZ, OVERBRIGHT CYMBALS, BRITTLE HI-HATS, "
    "THIN KICK, FLABBY BASS, BOOMY LOW END, MUD 200-400HZ, BOXINESS 300-600HZ, "
    "HARSHNESS 2.5-5KHZ, FLAT 2D MIX, MONO-COLLAPSED WIDTH, PHASEY STEREO, "
    "GENERIC AI REVERB, WASHED-OUT VOCAL FX, SMEARED TRANSIENTS, OVERCOMPRESSED BUS, "
    "LIMITER PUMPING, CLIPPING, DISTORTED MASTER, DULL TOP END, MASKED VOCALS, "
    "MASKED KICK/BASS, BUSY ARRANGEMENT, CONSTANT STACKING, CHEAP SYNTH PRESETS, "
    "FAKE ACOUSTIC INSTRUMENTS, LIFELESS MIDI, GENERIC BUBBLEGUM LYRICS, CLICHE RHYMES, "
    "VAGUE EMOTIONS, FORCED CUTENESS, FAKE EXCITEMENT, OVERLY CHILDISH DELIVERY, "
    "WUB BASS DROPS, TRAP HIHAT ROLLS, HUMMING INTRO, SPOKEN INTRO, LONG FADE OUT, "
    "DEATH GROWL, SCREAMING METAL"
)

_BANNED_WORDS_RE = re.compile(
    r"neon|tapestry|echoes|whispers|ignite|labyrinth|beacon|abyss|ethereal|celestial|kaleidoscope|cacophony|intertwined|ember|ephemeral|unfurl|unveil|nexus|testament|resonate|uncharted|illuminate|delve|chrysalis|transcend|twitter|wikipedia|http|www\.|subscribe|click here|looking forward to the game|"
    r"custom version|\.com\b|youtube|facebook",
    re.I,
)


def _is_valid_lyric_line(ln: str) -> bool:
    if not ln:
        return False
    if _BANNED_WORDS_RE.search(ln):
        return False
    if re.search(r"[_]{3,}|[-]{4,}|[=]{3,}", ln):
        return False
    if re.search(r"[가-힣一-龥ぁ-ゟ]", ln):
        return False
    letters = len(re.findall(r"[A-Za-z]", ln))
    if letters < 4 or letters / max(len(ln), 1) < 0.4:
        return False
    words = re.findall(r"[A-Za-z']+", ln)
    if not (2 <= len(words) <= 18):
        return False
    return True


class ScansionLLM:
    """Neural language model wrapper for Scansion-LM autoregressive lyric generation."""

    _instance: ScansionLLM | None = None

    def __init__(self, model_dir: str | Path | None = None) -> None:
        self.model_dir = self._resolve_model_path(model_dir)
        self.tok = None
        self.model = None
        self._loaded = False

    @classmethod
    def get_instance(cls, model_dir: str | Path | None = None) -> ScansionLLM:
        if cls._instance is None:
            cls._instance = ScansionLLM(model_dir)
        return cls._instance

    def _resolve_model_path(self, path: str | Path | None) -> Path | str:
        if path and Path(path).exists():
            return Path(path)
        for cand in CANDIDATE_PATHS:
            if (cand / "config.json").exists() and (
                (cand / "model.safetensors").exists() or (cand / "pytorch_model.bin").exists()
            ):
                return cand
        return "distilgpt2"

    def load(self) -> None:
        if self._loaded:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        src = str(self.model_dir)
        print(f"[*] Loading Scansion-LM from: {src} ...")
        self.tok = AutoTokenizer.from_pretrained(src)
        self.model = AutoModelForCausalLM.from_pretrained(src)
        if self.tok.pad_token_id is None:
            self.tok.pad_token = self.tok.eos_token or "<|endoftext|>"
        self.model.eval()

        try:
            from src.hardware import optimize_model_for_hardware, get_hardware_info
            self.model = optimize_model_for_hardware(self.model)
            hw = get_hardware_info()
            print(f"[+] Scansion-LM hardware acceleration: {hw['summary']}")
        except Exception as ex:
            print(f"[!] Info: Scansion-LM hardware fallback: {ex}")

        self._loaded = True
        print("[+] Scansion-LM loaded successfully.")

    def generate_continuation(
        self,
        prompt: str,
        max_new: int = 80,
        temperature: float = 0.85,
        do_sample: bool = True,
    ) -> str:
        self.load()
        import torch
        from src.hardware import get_optimal_device

        device = get_optimal_device()
        enc = self.tok(prompt, return_tensors="pt")
        enc = {k: v.to(device) for k, v in enc.items()}
        prompt_len = enc["input_ids"].shape[1]
        eos = self.tok.eos_token_id or self.tok.pad_token_id

        gen_kw: dict = {
            "max_new_tokens": max_new,
            "pad_token_id": self.tok.pad_token_id,
            "eos_token_id": eos,
            "use_cache": True,
            "repetition_penalty": 1.15,
            "no_repeat_ngram_size": 4,
        }
        if do_sample and temperature > 0:
            gen_kw.update(do_sample=True, top_k=50, top_p=0.92, temperature=float(temperature))
        else:
            gen_kw.update(do_sample=False)

        raw_model = self.model.module if hasattr(self.model, "module") else self.model
        with torch.no_grad():
            out = raw_model.generate(**enc, **gen_kw)
        new = self.tok.decode(out[0][prompt_len:], skip_special_tokens=False)
        for sp in ("<|endoftext|>", "<|end|>", "<|sheet|>", "<|brief|>"):
            if sp in new:
                new = new.split(sp, 1)[0]
        return new

    def generate_section_lines(
        self,
        title: str,
        idea: str,
        kind: str,
        n_lines: int = 4,
    ) -> list[str]:
        clean_idea = re.sub(r"\[[^\]]+\]", "", idea)
        clean_idea = re.sub(r"\([^)]*max[^)]*\)", "", clean_idea, flags=re.I)
        clean_idea = re.sub(r"\s+", " ", clean_idea).strip()[:100]
        prompt = f"Title: {title}\nIdea: {clean_idea}\n{kind}:\n"
        lines: list[str] = []
        for t in (0.75, 0.85, 0.95):
            curr_prompt = prompt if not lines else prompt + "\n".join(lines) + "\n"
            chunk = self.generate_continuation(curr_prompt, max_new=min(24 * n_lines, 140), temperature=t)
            for raw in chunk.replace(".", ".\n").splitlines():
                ln = raw.strip().strip('"').strip("'")
                if not ln or ln.startswith(("Title:", "Idea:", "STYLE:", "LYRICS:", "[", "<|")):
                    continue
                ln = re.sub(r"^[\W_]+", "", ln).strip()
                ln = re.sub(r"\s+", " ", ln)
                if len(ln) > 95:
                    ln = ln[:95].rsplit(" ", 1)[0].strip()
                if not _is_valid_lyric_line(ln):
                    continue
                if ln.lower() not in {x.lower() for x in lines}:
                    lines.append(ln)
                if len(lines) >= n_lines:
                    break
            if len(lines) >= n_lines:
                break
            if len(lines) >= max(2, (n_lines + 1) // 2) and t >= 0.85:
                break

        # If LLM gave fewer lines than requested, pad with contextual lyrical continuations
        if not lines:
            lines = [
                f"Count the marks behind the door",
                f"We live in a city that forgot the score",
                f"One night was all it took to fall",
                f"Now there's a new name written on the wall",
            ][:n_lines]
        return lines[:n_lines]

    def generate_full_song_lyrics(
        self,
        title: str,
        idea: str,
        structure: list[str] | None = None,
        mode: str = "3k",
    ) -> str:
        """Generate full structured song lyrics tailored for 3k or 5k Suno character limits."""
        if mode == "5k":
            # Extended master opus arrangement ~4,200 - 4,900 chars
            sec_map = [
                ("[Intro: Atmospheric Build, Filtered Lead-in]", "Intro", 4),
                ("[Verse 1: Close Dry Vocals, Narrative Pocket]", "Verse", 10),
                ("[Pre-Chorus: Rhythmic Tension Build]", "Pre-Chorus", 4),
                ("[Chorus: Wide Stereo Belt, Anthemic]", "Chorus", 8),
                ("[Post-Chorus: Catchy Vocal Hook & Ad-libs]", "Chorus", 4),
                ("[Verse 2: Intimate Pocket, Syllabic Detail]", "Verse", 10),
                ("[Pre-Chorus: Dynamic Lift]", "Pre-Chorus", 4),
                ("[Chorus: Wide Stereo Belt, Anthemic]", "Chorus", 8),
                ("[Verse 3 / Breakdown: Sparse Arrangement, Raw Vocals]", "Verse", 8),
                ("[Bridge: High Emotional Tension, Key Lift]", "Bridge", 8),
                ("[Instrumental Solo / Breakdown: Heavy Drums Build]", "Intro", 2),
                ("[Pre-Chorus: Final Suspense, Metronome Breath]", "Pre-Chorus", 4),
                ("[Final Chorus: Maximum Energy, Doubled Octaves, Ad-libs]", "Chorus", 10),
                ("[Outro: Extended Fading Echo, Sudden Cut]", "Outro", 4),
            ]
        else:
            # Compact radio master arrangement ~2,500 - 3,000 chars
            sec_map = [
                ("[Intro]", "Intro", 2),
                ("[Verse 1]", "Verse", 8),
                ("[Pre-Chorus]", "Pre-Chorus", 4),
                ("[Chorus]", "Chorus", 8),
                ("[Post-Chorus]", "Chorus", 4),
                ("[Verse 2]", "Verse", 8),
                ("[Pre-Chorus]", "Pre-Chorus", 4),
                ("[Chorus]", "Chorus", 8),
                ("[Bridge]", "Bridge", 6),
                ("[Final Chorus]", "Chorus", 8),
                ("[Outro]", "Outro", 2),
            ]

        blocks: list[str] = []
        chorus_lines: list[str] = []
        pre_chorus_lines: list[str] = []

        for tag, kind, count in sec_map:
            # Re-use the hook chorus and pre-chorus across repeats for song coherence
            if kind == "Chorus" and chorus_lines:
                lines = chorus_lines
            elif kind == "Pre-Chorus" and pre_chorus_lines:
                lines = pre_chorus_lines
            elif kind == "Intro":
                lines = [f"Red light in a glass box", f"Smile like a verdict"] if count <= 2 else [
                    "Red light in a glass box",
                    "Smile like a verdict",
                    "Count the marks behind the door",
                    "We live in a city that forgot the score",
                ][:count]
            elif kind == "Outro":
                lines = [f"Hard stop"] if count <= 2 else [
                    "Echo out into the night",
                    "No apology, no rewrite",
                    "One last strike against the screen",
                    "Hard stop",
                ][:count]
            else:
                lines = self.generate_section_lines(title, idea, kind, count)
                if kind == "Chorus" and not chorus_lines:
                    chorus_lines = lines
                elif kind == "Pre-Chorus" and not pre_chorus_lines:
                    pre_chorus_lines = lines

            stanza = f"{tag}\n" + "\n".join(lines)
            blocks.append(stanza)

        return "\n\n".join(blocks)


def generate_suno_v6_payload(
    theme: str = "dark glam electropop, cold radio pop, cinematic dance-pop",
    title: str = "New Name on the Door",
    *,
    tier: str = "high",
    vocal_gender: str = "f",
    bpm: int = 122,
    style_weight: float = 0.84,
    weirdness_constraint: float = 0.34,
    audio_weight: float = 0.0,
    model_version: str = "V6",
    engine: str = "hybrid",
    mode: str = "3k",
    custom_style: str = "",
    custom_negative: str = "",
    reference_catalog=None,
    reference_model=None,
    ref_model=None,
) -> dict[str, Any]:
    if ref_model is not None and reference_model is None:
        reference_model = ref_model
    """
    Generate the official Suno V6 Studio JSON payload matching the target specification:
    {
      "customMode": true,
      "instrumental": false,
      "model": "V6",
      "title": "...",
      "vocalGender": "f",
      "styleWeight": 0.84,
      "weirdnessConstraint": 0.34,
      "audioWeight": 0.0,
      "style": "[AUDIO_QUALITY] (MAX)\n...\n[STYLE: ...]",
      "negativeTags": "...",
      "prompt": "[Intro]\n..."
    }
    """
    # 1. Resolve Title
    final_title = title.strip() if title and title.strip() else "New Name on the Door"

    target_chars = 5000 if str(mode).lower() == "5k" else 3000
    try:
        from src.song_creator import build_calibrated_payload
        payload = build_calibrated_payload(
            title=final_title,
            theme=theme,
            target_chars=target_chars,
            vocal_gender=vocal_gender,
            bpm=bpm,
            style_weight=style_weight,
            weirdness_constraint=weirdness_constraint,
            audio_weight=audio_weight,
            model_version=model_version,
        )
        if custom_style:
            payload["style"] = custom_style.strip()
        if custom_negative:
            payload["negativeTags"] = custom_negative.strip()
        return payload
    except Exception as e:
        # Fallback to direct construction
        pass

    # 2. Resolve Lyrics via Scansion-LM or Statistical Reference Model
    if engine in ("llm", "hybrid"):
        llm = ScansionLLM.get_instance()
        lyrics = llm.generate_full_song_lyrics(final_title, theme, mode=mode)
    else:
        if reference_model is None:
            from src.inference import SongwritingReferenceModel
            reference_model = SongwritingReferenceModel()
        seed = reference_model.generate_prompt_seed(theme=theme, tier=tier, title=final_title)
        lyrics = seed.get("lyrics", "")

    # 3. Resolve Style of Music
    if custom_style and custom_style.strip():
        final_style = custom_style.strip()
    else:
        vocal_desc = (
            "BIG FEMALE BELT ON THE HOOK, CLOSE AND DRY ON THE VERSES"
            if vocal_gender.lower() == "f"
            else "RASPY MALE BELT ON THE HOOK, INTIMATE AND CLOSE ON THE VERSES"
        )
        theme_clean = theme.upper().strip()
        final_style = (
            f"{STUDIO_AUDIO_QUALITY_HEADER}\n"
            f"[STYLE: {theme_clean}. {bpm} BPM. GLOSSY, HUMAN, BITTER AND PHYSICAL. "
            f"{vocal_desc}. SOUND LIKE A REAL SINGER IN A TREATED MIDNIGHT BOOTH OVER "
            f"STACCATO SYNTH STABS, A COLD PIANO FIGURE, ANALOG CHORUS ON THE BED AND A TIGHT "
            f"LIVE-FEELING RHYTHM SECTION, CAPTURED WITH EXCELLENT MICROPHONES AND ENGINEERING. "
            f"NARROW MONO VERSE, WIDE CHORUS. FALLEN-STAR POP WITHOUT BECOMING PROTEST FOLK, "
            f"TRAP CONFESSION, OR MUSICAL-THEATRE MONOLOGUE.]"
        )

    # 4. Resolve Negative Tags
    negative_tags = custom_negative.strip() if custom_negative else DEFAULT_STUDIO_NEGATIVE_TAGS

    # 5. Build Complete V6 Payload
    payload = {
        "customMode": True,
        "instrumental": False,
        "model": model_version,
        "title": final_title,
        "vocalGender": vocal_gender.lower()[:1] if vocal_gender else "f",
        "styleWeight": float(style_weight),
        "weirdnessConstraint": float(weirdness_constraint),
        "audioWeight": float(audio_weight),
        "style": final_style,
        "negativeTags": negative_tags,
        "prompt": lyrics,
    }
    return payload


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate Suno V6 Studio JSON payload using Scansion-LM + Reference Model")
    parser.add_argument("--theme", default="DARK GLAM ELECTROPOP / COLD RADIO POP / CINEMATIC DANCE-POP", help="Theme/Genre style")
    parser.add_argument("--title", default="New Name on the Door", help="Song Title")
    parser.add_argument("--tier", default="high", choices=("low", "medium", "high", "viral"))
    parser.add_argument("--vocal", default="f", choices=("f", "m"), help="Vocal gender (f or m)")
    parser.add_argument("--bpm", type=int, default=122, help="BPM")
    parser.add_argument("--engine", default="hybrid", choices=("hybrid", "llm", "reference"))
    parser.add_argument("-o", "--out", default="", help="Optional output file for JSON payload")

    args = parser.parse_args()
    res = generate_suno_v6_payload(
        theme=args.theme,
        title=args.title,
        tier=args.tier,
        vocal_gender=args.vocal,
        bpm=args.bpm,
        engine=args.engine,
    )
    formatted = json.dumps(res, indent=2, ensure_ascii=False)
    print("\n" + formatted + "\n")

    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(formatted, encoding="utf-8")
        print(f"[+] Wrote Suno V6 payload to: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
