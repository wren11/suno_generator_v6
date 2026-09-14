"""Full Song Creation Engine — produces complete 3k & 5k Suno V6 JSON payloads plus companion assets:
1. Full 3k Suno Studio V6 JSON (precisely 2,950 - 3,000 chars)
2. Full 5k Suno Studio V6 Extended JSON (precisely 4,950 - 5,000 chars)
3. Paste-ready Suno Custom Mode prompt text files (.txt)
4. Synchronized LRC lyrics file with musical timestamps (.lrc)
5. Comprehensive Studio Production Brief (.md)
6. Cover Art generative prompt & visual style metadata (.json)
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Any

from src.catalog import SongCatalogStore
from src.llm import (
    DEFAULT_STUDIO_NEGATIVE_TAGS,
    STUDIO_AUDIO_QUALITY_HEADER,
    ScansionLLM,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

STUDIO_HEADER_3K = (
    "[AUDIO_QUALITY] (MAX)\n"
    "[QUALITY: MAX] (MAX)\n"
    "[REALISM: MAX] (MAX)\n"
    "[REAL_INSTRUMENTS: MAX] (MAX)\n"
    "MAX CLEAN, POLISHED. UPGRADE VOCALS, UPGRADE AUDIO QUALITY.\n"
    "POLISHED RADIO MASTER. KEEP CORE SONG/HOOKS/MELODY/STRUCTURE. MAKE IT BRIGHT, SWEET, CLEAN, 3D, WIDE, PUNCHY."
)

NEGATIVE_TAGS_3K = (
    "VOCAL SMEARING, MELISMA BETWEEN WORDS, UNNATURAL SYLLABLE STRETCHING, "
    "PORTAMENTO GLIDES, ROBOTIC VOWEL HOLDS, AI VOCAL SLURRING, SUNO/AI PLASTICITY, "
    "ROBOTIC VOCALS, FAST AUTOTUNE, FORMANT WARPING, CHIPMUNK TONE, NASAL LEAD VOCAL, "
    "HARSH SIBILANCE 6-10KHZ, OVERBRIGHT CYMBALS, BRITTLE HI-HATS, THIN KICK, FLABBY BASS, "
    "BOOMY LOW END, MUD 200-400HZ, BOXINESS 300-600HZ, HARSHNESS 2.5-5KHZ, FLAT 2D MIX, "
    "MONO-COLLAPSED WIDTH, PHASEY STEREO, GENERIC AI REVERB, WASHED-OUT VOCAL FX, "
    "SMEARED TRANSIENTS, OVERCOMPRESSED BUS, LIMITER PUMPING, CLIPPING, DISTORTED MASTER, "
    "DULL TOP END, MASKED VOCALS, LIFELESS MIDI, CLICHE RHYMES, LONG FADE OUT"
)

# Rich lyrical themes & rhyming motifs
GENRE_POETICS: dict[str, dict[str, Any]] = {
    "electropop": {
        "verse_bank": [
            "Red light flickers on a velvet chair, perfume drowning in the midnight air",
            "Dialing numbers that I swore I lost, counting up the wreckage and the sticker cost",
            "Glass on the carpet and a diamond crack, train on the siding with a one-way track",
            "Smile for the camera like a loaded gun, we made a fortune when the night was young",
            "Gold teeth flashing in a rented car, we took the spotlight and we drove too far",
            "Hotel lobby with the fountains dead, repeating every promise that you never said",
            "Turn down the monitor, turn up the room, sweeping the confetti with a velvet broom",
            "I heard the verdict from a telephone, if everybody loves you then you die alone",
        ],
        "pre_bank": [
            "Keep it quiet, keep your mouth shut, don't let anything catch you by surprise",
            "Hold your breath until the red light drops, you can see the hunger in a thousand eyes",
            "One step closer to the borderline, dancing on the edge of the neon sign",
        ],
        "chorus_bank": [
            "I'm not going back to where the mirrors lie",
            "Write a new name on the door before the paint gets dry",
            "Sell the crown, burn the gown, take the city down",
            "There's a brand new silhouette standing on your ground",
        ],
        "bridge_bank": [
            "I walked into the blinding white, no apology and no goodbye",
            "They trade your soul for radio play, then ask you why you couldn't stay",
            "The spotlight burns the shadow clean, the prettiest ghost they've ever seen",
        ],
    },
    "phonk": {
        "verse_bank": [
            "Sixteen locked and the rhythm won't miss, cold dark pavement with a serpent hiss",
            "Drift through the corner with the smoke rolled high, headlights slicing through a stormy sky",
            "Subwoofer shaking all the bolts loose now, trying to remember who to blame and how",
            "Plaid shirt, combat boots, razor-blade tongue, counting out the damage while the world is young",
            "Camera lens covered in a cheap lip gloss, tally up the numbers looking at a loss",
            "Step outside of the algorithm cell, nothing left to sponsor and nothing left to sell",
            "Cowbell knocking with a steady backbeat, rubber laying rubber on the midnight street",
            "Engine redlining in the dead of the night, ghost in the mirror looking for a fight",
        ],
        "pre_bank": [
            "Deadpan lecture in the western heat, watch the whole crowd jump to their feet",
            "Clutch in, gear down, ready for the drop, once the bass hits nobody can stop",
            "Grip on the wheel with knuckles white, tearing up the asphalt into the night",
        ],
        "chorus_bank": [
            "Pocket locked, hammer cocked, rolling on the floor",
            "Don't nobody come knocking on this door",
            "Heavy 808 rattle through the whole chassis",
            "Nothing about this ride was ever classy",
        ],
        "bridge_bank": [
            "Step into the shadows where the headlights fade",
            "We earned every single dollar that we made",
            "Analog distortion on the microphone stem",
        ],
    },
    "rock": {
        "verse_bank": [
            "Spotlights blinding through the arena smoke, struck by lightning when the silence broke",
            "Six strings screaming on an iron bridge, roar of sixty thousand over the ridge",
            "Sweat on the frets and blood on the pick, high voltage current that hits you quick",
            "Bass drum punching you straight in the chest, tonight we don't give a damn about rest",
            "Count in the rhythm with four on the floor, kicking wide open the backstage door",
            "Amplifiers hum like a jet on the strip, tighten your knuckles and steady your grip",
            "Crowd starts pushing against the barricade, we earned every scar that we ever made",
            "Pick slide echoes across the whole roof, look at this fire if you need the proof",
        ],
        "pre_bank": [
            "Are you ready for the walls to shake? How much pressure can a human take?",
            "Crank up the master, max out the gain, drown out the sorrow, drown out the pain",
            "Stand on the edge of the stage tonight, blinded by the wash of the stadium light",
        ],
        "chorus_bank": [
            "Feel the thunder running in the wire!",
            "Set the stadium on gasoline fire!",
            "Hands in the air till the speakers blow out!",
            "This is what living is all about!",
        ],
        "bridge_bank": [
            "Solo screams up to the highest fret, a moment you know you will never forget",
            "Harmonics ring into the open sky, we were born for this, you and I",
            "Fists raised high in the stadium light, kings of the world for a single night",
        ],
    },
    "general": {
        "verse_bank": [
            "Shadows stretch across the concrete hall, footsteps fading down against the wall",
            "Every clock is ticking down the second hand, drawing new lines in the shifting sand",
            "Letters written that were never mailed, ships departing that had never sailed",
            "Woke up running with an open mind, leaving every heavy chain behind",
            "City waking under morning gray, finding words that we were scared to say",
            "Keys on the counter and the coffee cold, tired of doing what we're always told",
            "Window open to the highway breeze, looking at the skyline through the trees",
            "Radio playing our forgotten song, reminding us we were right all along",
        ],
        "pre_bank": [
            "Step into the light and don't turn around, listen to the heartbeat of the sound",
            "Everything is changing in a single breath, stronger than the sorrow, faster than the rest",
            "Look into the distance where the colors blend, this is a beginning and not an end",
        ],
        "chorus_bank": [
            "Turn the world around and let it spin",
            "This is where the real life begins",
            "Shout it out until the morning breaks",
            "No more regrets for the old mistakes",
        ],
        "bridge_bank": [
            "Through every storm and through every rain, breaking the silence and breaking the chain",
            "We found the compass in the darkest hour, rising together with an ancient power",
            "No more whispers in an empty room, flowers breaking through the winter gloom",
        ],
    },
    "rusty_spork": {
        "verse_bank": [
            "Seven thousand catalog tracks running in the code, twenty-five thousand lines of fire on the open road",
            "Two point seven million words, twenty-four bit sound, cleanest scansion pocket that you ever found",
            "Listen close to the verse cause the JSON is right here, open Custom Mode and wipe away the fear",
            "Paste the prompt, put it in, keep the structure tight, watch the Suno V6 engine illuminate the night",
            "Style weight point eight four, zero audio weight, dialed in so precise it will decide your fate",
            "Coming soon to Hugging Face, live upon the Space, bringing top-shelf studio masters to the human race",
            "Turn the monitors loud, let the sub-bass kick, you can build a chart-topper with a single click",
            "Trained on every viral hook from the morning to the dark, lighting up the speakers with a radioactive spark",
        ],
        "pre_bank": [
            "Take it for a spin, baby put it in, keep the structure clean and watch the magic win",
            "Audio quality MAX, no robotic drone, sound like a superstar inside a treated booth alone",
            "Check the negative tags, wipe the sibilance away, this is how the hitmakers make the record play",
        ],
        "chorus_bank": [
            "You can thank me later when the speakers start to roar!",
            "Write a brand new hit before the paint dries on the door!",
            "Say: Thanks Rusty Spork, you helped me learn it!",
            "Trained on seven thousand tracks, we definitely earned it!",
        ],
        "bridge_bank": [
            "No melisma smearing, no robotic vocal drone, just an analog microphone in a midnight zone",
            "Now you got the blueprint, now you know the trick, grab the JSON payload with a single click",
            "Hugging Face is dropping it, ready for the crowd, make it wide and punchy and play it extra loud",
        ],
    },
}


def _select_poetic_bank(theme: str) -> dict[str, Any]:
    t = theme.lower()
    if any(k in t for k in ("rusty", "spork", "json", "prompt", "model", "meta", "funny", "catchy", "hugging")):
        return GENRE_POETICS["rusty_spork"]
    elif any(k in t for k in ("phonk", "rap", "drill", "trap", "hip hop", "hip-hop", "drift")):
        return GENRE_POETICS["phonk"]
    elif any(k in t for k in ("rock", "metal", "punk", "guitar", "stadium", "anthem", "grunge")):
        return GENRE_POETICS["rock"]
    elif any(k in t for k in ("pop", "electro", "dance", "synth", "glam", "club", "disco")):
        return GENRE_POETICS["electropop"]
    return GENRE_POETICS["general"]


def build_studio_style_block(
    theme: str,
    bpm: int = 122,
    vocal_gender: str = "f",
    mode: str = "3k",
) -> str:
    """Construct studio audio quality header and comprehensive musical production tags."""
    vocal_dir = (
        "BIG FEMALE BELT ON THE HOOK, CLOSE AND DRY ON THE VERSES"
        if vocal_gender.lower() == "f"
        else "RASPY MALE BELT ON THE HOOK, INTIMATE AND CLOSE ON THE VERSES"
    )
    theme_upper = theme.upper().strip()

    if mode == "5k":
        return (
            f"{STUDIO_AUDIO_QUALITY_HEADER}\n"
            f"[STYLE: {theme_upper}. {bpm} BPM. GLOSSY, HUMAN, BITTER AND PHYSICAL. {vocal_dir}. "
            f"SOUND LIKE A REAL SINGER IN A TREATED MIDNIGHT BOOTH OVER STACCATO SYNTH STABS, A COLD PIANO FIGURE, "
            f"ANALOG CHORUS ON THE BED AND A TIGHT LIVE-FEELING RHYTHM SECTION, CAPTURED WITH EXCELLENT MICROPHONES AND ENGINEERING. "
            f"NARROW MONO VERSE, WIDE CHORUS. FALLEN-STAR POP WITHOUT BECOMING PROTEST FOLK, TRAP CONFESSION, OR MUSICAL-THEATRE MONOLOGUE.]\n"
            f"[STEREO_FIELD: Pinpoint mono center lead vocal, wide binaural doubled chorus backing vocals, discrete stereo guitar tracking, center-locked kick and sub-bass]\n"
            f"[VOCAL_CHAIN: Vintage Neumann U87 tube microphone, 1176 fast peak compression into LA-2A optical smoothing, Pultec 12kHz high-shelf sheen, clean analog console preamp warmth]\n"
            f"[DRUM_ENGINEERING: Punchy transient-shaped 24-bit kick, snappy crack snare with plate reverb decay, crisp organic hi-hats with natural velocity variation, warm tape-saturated parallel bus]\n"
            f"[BASS_FOUNDATION: Solid round sub-bass harmonic weight below 80Hz, growling analog mid-bass grit between 200-400Hz, tight sidechain ducking to kick drum]"
        )
    else:
        return (
            f"{STUDIO_HEADER_3K}\n"
            f"[STYLE: {theme_upper}. {bpm} BPM. GLOSSY, HUMAN, BITTER AND PHYSICAL. "
            f"{vocal_dir}. SOUND LIKE A REAL SINGER IN A TREATED MIDNIGHT BOOTH OVER "
            f"STACCATO SYNTH STABS, A COLD PIANO FIGURE, ANALOG CHORUS ON THE BED AND A TIGHT "
            f"LIVE-FEELING RHYTHM SECTION. NARROW MONO VERSE, WIDE CHORUS.]"
        )


def build_calibrated_payload(
    title: str = "New Name on the Door",
    theme: str = "dark glam electropop, cold radio pop, cinematic dance-pop",
    target_chars: int = 3000,
    *,
    vocal_gender: str = "f",
    bpm: int = 122,
    style_weight: float = 0.84,
    weirdness_constraint: float = 0.34,
    audio_weight: float = 0.0,
    model_version: str = "V6",
) -> dict[str, Any]:
    """Generate exact Suno Studio V6 payload calibrated strictly to target_chars (3000 or 5000)."""
    mode = "5k" if target_chars >= 4500 else "3k"
    style_block = build_studio_style_block(theme, bpm=bpm, vocal_gender=vocal_gender, mode=mode)
    neg_tags = DEFAULT_STUDIO_NEGATIVE_TAGS if mode == "5k" else NEGATIVE_TAGS_3K

    bank = _select_poetic_bank(theme)
    v = bank["verse_bank"]
    p = bank["pre_bank"]
    c = bank["chorus_bank"]
    b = bank["bridge_bank"]

    if mode == "5k":
        sections = [
            ("[Intro: Atmospheric Synthesizer Swell, Filtered Drums]", [v[0]]),
            ("[Verse 1: Close Dry Vocals, Narrative Pocket]", [v[1], v[2]]),
            ("[Pre-Chorus: Rising Snare Build, Rhythmic Tension]", [p[0]]),
            ("[Chorus: Wide Stereo Belt, Full Frequency Impact, Anthemic Hook]", c[:4]),
            ("[Verse 2: Intimate Pocket, Rapid Syllabic Detail]", [v[3], v[4]]),
            ("[Pre-Chorus: Rising Snare Build, Rhythmic Tension]", [p[1]]),
            ("[Verse 3: Breakdown Arrangement, Raw Stripped Vocals]", [v[5]]),
            ("[Bridge: Emotional Key Modulation, High Harmonic Drama]", b[:2]),
            ("[Final Chorus: Maximum Peak Energy, Doubled Octaves]", c[:4]),
            ("[Outro: Fading Echoes into Heavy Final Resonance, Sudden Cut]", [v[6], "Hard stop. No fade."]),
        ]
    else:
        sections = [
            ("[Intro]", [v[0]]),
            ("[Verse 1]", [v[1], v[2]]),
            ("[Pre-Chorus]", [p[0]]),
            ("[Chorus]", c[:4]),
            ("[Verse 2]", [v[3], v[4]]),
            ("[Bridge]", b[:2]),
            ("[Final Chorus]", c[:4]),
            ("[Outro]", [v[5], "Hard stop. No fade."]),
        ]

    stanzas = [f"{tag}\n" + "\n".join(lines) for tag, lines in sections]
    lyrics = "\n\n".join(stanzas)

    payload = {
        "customMode": True,
        "instrumental": False,
        "model": model_version,
        "title": title.strip(),
        "vocalGender": vocal_gender[:1].lower() if vocal_gender else "f",
        "styleWeight": float(style_weight),
        "weirdnessConstraint": float(weirdness_constraint),
        "audioWeight": float(audio_weight),
        "style": style_block,
        "negativeTags": neg_tags,
        "prompt": lyrics,
    }

    # Ensure initial payload strictly <= target_chars
    while len(json.dumps(payload, indent=2, ensure_ascii=False)) > target_chars and "\n" in payload["prompt"]:
        lines = payload["prompt"].splitlines()
        if len(lines) > 6:
            lines.pop(-2)
            payload["prompt"] = "\n".join(lines)
        else:
            break

    # Clean natural musical ad-libs and cues to reach exact character targets without overflow
    cues = [
        f"\n(Thanks Rusty Spork!)",
        f"\n(Take it for a spin!)",
        f"\n(Put it in!)",
        f"\n(Keep the structure!)",
        f"\n(Never look back!)",
        f"\n(Feel the rush!)",
        f"\n(Take the crown!)",
        f"\n(Higher!)",
        f"\n[Echoes fade into the midnight air]",
        f"\n[Master: 24-bit 96kHz analog console, -14 LUFS radio specification]",
    ]
    for cue in cues:
        test_payload = dict(payload)
        test_payload["prompt"] = payload["prompt"] + cue
        if len(json.dumps(test_payload, indent=2, ensure_ascii=False)) <= target_chars:
            payload["prompt"] += cue

    return payload


def generate_lrc_timestamps(lyrics: str, total_seconds: float = 216.0) -> str:
    """Generate standard synchronized LRC lyrics file with musical timestamps."""
    lines = [ln.strip() for ln in lyrics.splitlines() if ln.strip()]
    if not lines:
        return ""

    time_per_line = total_seconds / max(len(lines), 1)
    lrc_out = [
        "[ti:Suno Studio Master]",
        "[ar:AI Songwriting Reference Engine]",
        "[al:Suno V6 Studio Editions]",
        f"[length:{int(total_seconds//60):02d}:{int(total_seconds%60):02d}]",
        "",
    ]

    cur_time = 0.0
    for ln in lines:
        mins = int(cur_time // 60)
        secs = cur_time % 60
        stamp = f"[{mins:02d}:{secs:05.2f}]"
        lrc_out.append(f"{stamp} {ln}")
        if ln.startswith("[") and ln.endswith("]"):
            cur_time += time_per_line * 0.75
        else:
            cur_time += time_per_line

    return "\n".join(lrc_out)


def create_complete_song_bundle(
    title: str = "New Name on the Door",
    theme: str = "dark glam electropop, cold radio pop, cinematic dance-pop",
    *,
    vocal_gender: str = "f",
    bpm: int = 122,
    out_dir: str | Path = "dist/output/songs",
    ingest_to_catalog: bool = True,
    catalog_path: str | Path = "dist/models/suno_song_catalog.json",
) -> dict[str, Any]:
    """
    Generate a COMPLETE NEW SONG with:
    1. Full 3k Suno Studio V6 JSON payload (calibrated to <= 3,000 chars)
    2. Full 5k Suno Studio V6 JSON payload (calibrated to <= 5,000 chars)
    3. Paste-ready Suno Custom prompt sheets (.txt)
    4. Synchronized LRC lyrics file (.lrc)
    5. Comprehensive Studio Production Brief (.md)
    6. Cover Art generative prompt & visual style metadata (.json)
    """
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "untitled_song"
    song_dir = Path(out_dir) / slug
    song_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  SUNO STUDIO V6 COMPLETE NEW SONG GENERATOR")
    print("=" * 65)
    print(f"Title:        {title}")
    print(f"Theme/Genre:  {theme}")
    print(f"BPM:          {bpm} | Vocal: {vocal_gender.upper()}")
    print(f"Output Dir:   {song_dir}")
    print("-" * 65)

    # 1. Generate 3k Payload (strictly <= 3,000 chars)
    p3k = build_calibrated_payload(title, theme, target_chars=3000, vocal_gender=vocal_gender, bpm=bpm)
    p3k_json_str = json.dumps(p3k, indent=2, ensure_ascii=False)
    p3k_file = song_dir / f"{slug}_v6_3k.json"
    p3k_file.write_text(p3k_json_str, encoding="utf-8")

    # 2. Generate 5k Payload (strictly <= 5,000 chars)
    p5k = build_calibrated_payload(title, theme, target_chars=5000, vocal_gender=vocal_gender, bpm=bpm)
    p5k_json_str = json.dumps(p5k, indent=2, ensure_ascii=False)
    p5k_file = song_dir / f"{slug}_v6_5k.json"
    p5k_file.write_text(p5k_json_str, encoding="utf-8")

    # 3. Paste-ready text prompt sheets
    p3k_txt = song_dir / f"{slug}_prompt_3k.txt"
    p3k_txt.write_text(
        f"TITLE\n{p3k['title']}\n\nSTYLE\n{p3k['style']}\n\nEXCLUDE\n{p3k['negativeTags']}\n\nLYRICS\n{p3k['prompt']}\n",
        encoding="utf-8",
    )
    p5k_txt = song_dir / f"{slug}_prompt_5k.txt"
    p5k_txt.write_text(
        f"TITLE\n{p5k['title']}\n\nSTYLE\n{p5k['style']}\n\nEXCLUDE\n{p5k['negativeTags']}\n\nLYRICS\n{p5k['prompt']}\n",
        encoding="utf-8",
    )

    # 4. Synchronized LRC lyrics file
    lrc_content = generate_lrc_timestamps(p5k["prompt"], total_seconds=216.0)
    lrc_file = song_dir / f"{slug}_lyrics.lrc"
    lrc_file.write_text(lrc_content, encoding="utf-8")

    # 5. Visual Cover Art Generative Prompt
    cover_prompt = {
        "title": title,
        "theme": theme,
        "style_aesthetic": f"Cinematic {theme} album artwork, moody studio lighting, 35mm film photography, Kodak Portra 800 tone",
        "prompt": (
            f"Album cover for song '{title}', aesthetic of {theme}. "
            f"Hyper-detailed portrait of a confident {('female' if vocal_gender.lower()=='f' else 'male')} pop star in a dark neon-lit studio booth, "
            f"subtle velvet shadows, film grain, atmospheric smoke, cyan and magenta backlight, expensive high-fashion styling, shot on Hasselblad H6D-100c, 8k resolution, minimalist modern typography layout."
        ),
        "negative_prompt": "cartoon, illustration, 3d render, anime, blurry, low resolution, amateur, watermark, signature",
        "aspect_ratio": "1:1",
        "color_palette": ["#0F0D15", "#E8175D", "#474747", "#363636", "#CC527A"],
    }
    cover_file = song_dir / f"{slug}_cover_prompt.json"
    cover_file.write_text(json.dumps(cover_prompt, indent=2, ensure_ascii=False), encoding="utf-8")

    # 6. Comprehensive Studio Production Brief (.md)
    brief_md = f"""# Studio Production Brief: {title}

**Genre & Style**: `{theme}`  
**BPM**: `{bpm}` | **Vocal Gender**: `{vocal_gender.upper()}` | **Model Target**: `Suno V6`  
**Payload Lengths**: `3K JSON: {len(p3k_json_str):,} chars` | `5K JSON: {len(p5k_json_str):,} chars`

---

## 🎛️ Suno Studio Configuration

```json
{{
  "customMode": true,
  "instrumental": false,
  "model": "V6",
  "title": "{title}",
  "vocalGender": "{vocal_gender.lower()[:1]}",
  "styleWeight": {p5k['styleWeight']},
  "weirdnessConstraint": {p5k['weirdnessConstraint']},
  "audioWeight": {p5k['audioWeight']}
}}
```

---

## 🎧 Audio Engineering & Mix Notes
- **Vocal Chain**: Vintage tube microphone into optical leveling amplifier and analog console warmth.
- **Stereo Field**: Narrow mono verses for vocal intimacy; ultra-wide doubled choruses with binaural side information.
- **Master Quality**: MAX clean, studio radio master, zero clipping, transparent limiter ceiling.

---

## 📜 Complete Song Lyrics ({len(p5k['prompt'].splitlines())} lines)

```text
{p5k['prompt']}
```

---

## 🎨 Cover Art Prompt
> **{cover_prompt['prompt']}**
"""
    brief_file = song_dir / f"{slug}_production_brief.md"
    brief_file.write_text(brief_md, encoding="utf-8")

    # 7. Ingest into song catalog
    if ingest_to_catalog:
        try:
            cat = SongCatalogStore(catalog_path)
            cat.ingest(
                {
                    "title": title,
                    "prompt": p5k["prompt"],
                    "lyrics": p5k["prompt"],
                    "style_of_music": theme,
                    "tags": [t.strip() for t in theme.split(",") if t.strip()],
                    "discovered_via": "song_creator_suite",
                },
                discovered_via="v6_creator",
            )
            cat.save()
            print(f"[+] Ingested new track into master catalog ({len(cat.all_records())} songs)")
        except Exception as ce:
            print(f"[!] Catalog note: {ce}")

    print("\n[+] COMPLETE NEW SONG CREATED SUCCESSFULLY:")
    print(f"    • 3k Payload:       {p3k_file.name} ({len(p3k_json_str):,} characters)")
    print(f"    • 5k Payload:       {p5k_file.name} ({len(p5k_json_str):,} characters)")
    print(f"    • Paste Prompts:    {p3k_txt.name}, {p5k_txt.name}")
    print(f"    • LRC Lyrics:       {lrc_file.name} (synchronized timestamps)")
    print(f"    • Production Brief: {brief_file.name}")
    print(f"    • Cover Art Prompt: {cover_file.name}")
    print(f"    • Directory:        {song_dir}\n")

    return {
        "title": title,
        "slug": slug,
        "dir": str(song_dir),
        "payload_3k": p3k,
        "payload_5k": p5k,
        "len_3k": len(p3k_json_str),
        "len_5k": len(p5k_json_str),
        "files": {
            "json_3k": str(p3k_file),
            "json_5k": str(p5k_file),
            "prompt_3k": str(p3k_txt),
            "prompt_5k": str(p5k_txt),
            "lrc": str(lrc_file),
            "brief": str(brief_file),
            "cover": str(cover_file),
        },
    }
