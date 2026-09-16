"""Build the training corpus from hit DNA + original lyric extracts."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

from .extract import extract_song
from .paths import CORPUS_JSONL, HITS_JSON, SEED_EXTRACTS, USER_EXTRACTS

BOS_BRIEF = "<|brief|>"
BOS_SHEET = "<|sheet|>"
EOS = "<|end|>"

THEMES = {
    "desert": {
        "titles": ["Heat Line", "Mojave Bars", "Dry Mouth", "Red Mile", "Salt Wind"],
        "ideas": [
            "A man scraping survival out of desert heat, stubborn will over panic.",
            "Walking a cracked highway until the sun becomes a verdict.",
            "Third-person dust and thirst turning into a vow to keep moving.",
        ],
        "genre": [("Rock", 70), ("Thrash metal", 30)],
        "vocal": ("male", "Baritone", "Raspy, gritty, chest-forward"),
        "tempo": ("Allegro", 115, "4/4"),
        "energy": 78,
        "form": "standard",
        "rhyme": "ABAB",
        "v": [
            "He scrapes at the basin for a mouthful of shade",
            "The highway keeps humming a colorless note",
            "Dust writes his name on the back of his throat",
            "He bargains with miles that do not negotiate",
            "A buzzard keeps counting the heat on his back",
            "The canteen says almost, then nothing, then wait",
            "He laughs at the sky like a dare he can take",
            "The bones of the radio cough up a hymn",
        ],
        "c": [
            "Keep walking, keep walking, the sun is a fist",
            "Keep walking, keep walking, refuse to exist",
            "as a rumor of water, a trick of the dust",
            "Keep walking, keep walking, because you must",
        ],
        "pre": ["The light gets louder", "The ground gets thinner"],
        "br": [
            "If the night ever comes it will come like a debt",
            "He still has a name that the heat has not kept",
            "He still has a step he can spend without rest",
            "He still has a breath he can spend on the west",
        ],
        "style_extra": "Drop-D guitars, snare crack, dry mid-forward mix",
        "dna": "Trochaic punches in chorus; spondee title hits; extra blank line before the belt",
        "tags": ("[Verse 1: Percussive, Guitar Focus]", "[Chorus: Powerful Vocals]", "[Bridge: Building Intensity]"),
    },
    "night": {
        "titles": ["As It Stays", "Blinding Exit", "Afterglow Lane", "Empty Freeway", "Neon Debt"],
        "ideas": [
            "Driving the empty freeway after a fight you cannot unsay.",
            "City still lit. Windows down so the night can argue back.",
            "Falsetto confession over four-on-the-floor, no resolution.",
        ],
        "genre": [("Synth-pop", 80), ("Dance-pop", 20)],
        "vocal": ("male", "Falsetto lead", "Whisper to belt dynamics"),
        "tempo": ("Allegro", 171, "4/4"),
        "energy": 72,
        "form": "anthem",
        "rhyme": "ABAB",
        "v": [
            "The dashboard keeps time with a pulse I can fake",
            "Your name is a streetlight that will not go dim",
            "I left you a sentence I cannot unsay",
            "The city still wears last night on its skin",
            "I count every exit I do not take",
            "The radio sells me a softer mistake",
            "The overpass carries a river of red",
            "I mouth the apology into the wheel",
        ],
        "c": [
            "I keep the windows down so the night can talk",
            "I keep the windows down till the feeling walks",
            "I keep the windows down, I do not turn back",
            "I keep the windows down on the blinding track",
        ],
        "pre": ["The riff is a warning", "The kick is a clock"],
        "br": [
            "If I make it to morning I still have your coat",
            "If I make it to morning I still have the note",
        ],
        "style_extra": "Pulsing synth bass, gated snare, analog lead",
        "dna": "The riff is the hook. Lyrics chase it. Kinetic night-drive images.",
        "tags": ("[Verse 1: Rhythmic, Synth Focus]", "[Chorus: Falsetto Lead, Doubled]", "[Post-Chorus: Non-lexical]"),
    },
    "country": {
        "titles": ["Choosin' Home", "County Line", "Real Name", "Two-Lane Mercy", "Porch Light"],
        "ideas": [
            "Leaving a city love for the place that still knows your real name.",
            "Pride and ache in the same sentence. Truck-cab confession to a bar chorus.",
            "A decision that sounds like a map.",
        ],
        "genre": [("Country", 75), ("Country pop", 25)],
        "vocal": ("female", "Mezzo-soprano", "Belted, anthemic, open throat"),
        "tempo": ("Moderato", 148, "4/4"),
        "energy": 68,
        "form": "country",
        "rhyme": "ABCB",
        "v": [
            "I packed up the apartment in a grocery bag",
            "Left your coffee mug for the next mistake",
            "The skyline kept waving like it wanted me back",
            "I did not wave. I just put it in drive",
            "Mama still sets out a plate like she knows",
            "The porch light is stubborn. It never learned no",
            "The radio preaches a two-lane gospel",
            "I fold up the skyline and leave it on read",
        ],
        "c": [
            "I am choosin' the long way, choosin' the dust",
            "I am choosin' the people who still know my name",
            "I am choosin' the quiet that I can trust",
            "I am choosin' the town that will say it the same",
        ],
        "pre": ["Tell the city I tried", "Tell the city goodbye"],
        "br": [
            "If loving you cost me the sound of my voice",
            "I am spending the rest on a cheaper choice",
        ],
        "style_extra": "Telecaster twang, snare crack, gang hey, fiddle/steel",
        "dna": "Story verse names objects. Chorus restates the decision in plain speech. Title on a downbeat.",
        "tags": ("[Verse 1: Story, Guitar Lick]", "[Chorus: Belted, Gang Vocals]", "[Bridge: Reflective]"),
    },
    "quiet": {
        "titles": ["Birds We Aren't", "Someone Still", "Soft Ledger", "Unsent", "Hold Still"],
        "ideas": [
            "Admitting you still wait for someone who already moved on.",
            "Soft until it isn't. The chorus is the thing you never said in the room.",
            "Close-mic confession, whispered verses, exploding last chorus.",
        ],
        "genre": [("Alt-pop", 60), ("Indie folk", 40)],
        "vocal": ("female", "Alto", "Intimate, close-mic, breathy"),
        "tempo": ("Andante", 96, "4/4"),
        "energy": 42,
        "form": "ballad",
        "rhyme": "XAXA",
        "v": [
            "I keep your cup in the sink like a maybe",
            "The hallway still knows how you said my name",
            "I practice the sentence and never quite say it",
            "The quiet is doing the work of the flame",
            "I leave the porch light on for a ghost",
            "Your coat is a rumor that lives on the chair",
            "I count the cups we said we would wash",
            "The kettle still clicks like it knows you are there",
        ],
        "c": [
            "I am still in the doorway you already left",
            "I am still in the doorway, I have not moved yet",
            "I am still in the doorway, I call it a debt",
            "I am still in the doorway. I cannot forget",
        ],
        "pre": ["Do not make me louder", "Do not make me kind"],
        "br": [
            "If I say it in daylight it might become true",
            "So I say it in whispers the way I say you",
        ],
        "style_extra": "Soft kick, warm bass, close sibilance, airy chorus",
        "dna": "Few words, long notes. Avoid spondees. Extra blank lines. Parenthetical whispers.",
        "tags": ("[Verse 1: Whispered, Sparse]", "[Chorus: Open Vowels]", "[Bridge: Bare]"),
    },
    "club": {
        "titles": ["Say It", "Steel Night", "The Drop Has a Name", "Until Dawn", "Call Me Twice"],
        "ideas": [
            "A night that refuses to end. Bodies, lights, a name said like a spell.",
            "The drop is the title. Four-bar chant hook.",
            "Stacked vocals, call and response, no essay in the chorus.",
        ],
        "genre": [("House", 55), ("Dance-pop", 45)],
        "vocal": ("unspecified", "Unspecified", "Choir stacked harmonies"),
        "tempo": ("Allegro", 124, "4/4"),
        "energy": 82,
        "form": "edm",
        "rhyme": "ABCABC",
        "v": [
            "The floor is a rumor the bass makes true",
            "Your name is a strobe I can almost hold",
            "We spend the same hour until it is new",
            "We spend the same hour until we are gold",
            "The smoke writes a circle I step inside",
            "Your laugh is a siren the speakers repeat",
            "We trade the same glance until it is law",
            "The ceiling keeps raining a silver receipt",
        ],
        "c": [
            "Say it, say it, let the night decide",
            "Say it, say it, keep me on the line",
            "Say it, say it, we do not sit down",
            "Say it, say it, burn the whole town",
        ],
        "pre": ["Build it, hold it", "Wait for the floor"],
        "br": [
            "If the morning arrives we can owe it a lie",
            "If the morning arrives we can still be this high",
        ],
        "style_extra": "Four-on-the-floor, sidechain pads, gang vocals, club steel",
        "dna": "Chorus lines equal length. Post-chorus is a chant. Leave space for the drop.",
        "tags": ("[Verse 1: Groove]", "[Build]", "[Drop, Hook]", "[Chorus: Stacked, Call and Response]"),
        "call": True,
    },
    "rap": {
        "titles": ["Not That", "Keep Count", "Janice, Quiet", "West Pocket", "Name Play"],
        "ideas": [
            "Conversational verse density, then a four-bar singable hook.",
            "Do not fill every bar. Leave extra lines as space for the beat.",
            "The hook is a chant, not a paragraph.",
        ],
        "genre": [("Hip-hop", 70), ("Trap", 30)],
        "vocal": ("male", "Spoken-sung", "Rap-sung hybrid"),
        "tempo": ("Moderato", 96, "4/4"),
        "energy": 64,
        "form": "rap",
        "rhyme": "AABB",
        "v": [
            "I talk to the ceiling like it owes me rent",
            "I talk to the ceiling like the night is a tent",
            "I filed every favor under do not repeat",
            "I filed every number under do not delete",
            "They wanted a villain, I handed a list",
            "They wanted a villain, I handed a fist of quiet",
        ],
        "c": [
            "We not like that, we not like that",
            "Keep my name out your mouth if you cannot keep facts",
            "We not like that, we not like that",
            "Four words, one pocket, do not come back",
        ],
        "pre": ["Tag.", "Hold."],
        "br": ["Break the loop. Count it. Come home."],
        "style_extra": "Sparse 808, dry vocal, dark piano loop",
        "dna": "Hook is a chant. Verses rhythmic first. Repeat a four-word title as percussion.",
        "tags": ("[Verse 1: Percussive, Dry]", "[Hook: Chant]", "[Verse 2: Denser Internals]"),
    },
    "soul": {
        "titles": ["Die With the Light", "Lose the Wheel", "Ordinary Prayer", "Shallow End", "Keep the Vow"],
        "ideas": [
            "Romantic apocalypse said as an idiom. Duet altitudes.",
            "Verses confess. Chorus detonates. Title held on a long note.",
            "Gospel stacks in parentheses. Live band language.",
        ],
        "genre": [("Soul", 60), ("Pop", 40)],
        "vocal": ("duet", "Tenor", "Belted, anthemic, open throat"),
        "tempo": ("Adagio", 80, "6/8"),
        "energy": 70,
        "form": "ballad",
        "rhyme": "ABAB",
        "v": [
            "If the world gets smaller I still want your hand",
            "If the world gets quieter I still want the band",
            "You count every mercy like a bill we can pay",
            "I count every morning we still get to stay",
            "I put down the armor I wore as a child",
            "You take off the hurry that lived in your jaw",
            "The kitchen becomes a cathedral at dusk",
            "We practice forever in ordinary light",
        ],
        "c": [
            "I would die with a smile if the smile was yours",
            "I would die with a smile on the kitchen floor",
            "I would die with a smile, that is all I have stored",
            "I would die with a smile. I am not keeping score",
        ],
        "pre": ["Hold the note", "Let it climb"],
        "br": [
            "If faith is a room then we already moved in",
            "If faith is a room then the lock is your grin",
        ],
        "style_extra": "Live piano, organ, snare on 2/4, wide analog chorus",
        "dna": "Call-and-response duet. Title is an idiom. Harmonies in parentheses.",
        "tags": ("[Verse 1: Piano, Male Vocals]", "[Chorus: Duet, Gospel Stacks]", "[Bridge: Choir]"),
        "call": True,
    },
    "folk": {
        "titles": ["Yellow Coat", "Riptide Two", "Postcard Chicago", "Wonderwall Adjacent", "Counting Hours"],
        "ideas": [
            "One color, one devotion. Simple language. Let the title vowel ring.",
            "Specific crumbs in verses. Chorus is the undertow.",
            "Strummed anthem. Gang on the last chorus. Do not overwrite.",
        ],
        "genre": [("Folk", 55), ("Indie pop", 45)],
        "vocal": ("male", "Tenor", "Conversational, dry, present"),
        "tempo": ("Andante", 102, "4/4"),
        "energy": 50,
        "form": "standard",
        "rhyme": "ABCB",
        "v": [
            "I bought you a jacket the color of noon",
            "You wore it on Tuesdays and never explained",
            "The river kept pulling the boats out of tune",
            "I stayed on the bank like a man who was trained",
            "The photograph curls at the edge of the frame",
            "You hummed in the doorway and borrowed my keys",
            "The highway is quiet, the yellow coat stays",
            "I measure the hours in coffee and leaves",
        ],
        "c": [
            "Look at the water, look at it go",
            "Look at the water, I already know",
            "Look at the water, I cannot swim home",
            "Look at the water, I do it alone",
        ],
        "pre": ["Take me under", "Say it slow"],
        "br": [
            "If I am your savior I am badly cast",
            "If I am your savior this will not last",
        ],
        "style_extra": "Acoustic strum, stomps, dry vocal, tambourine",
        "dna": "Mantra writing. One proverb-like image. Cool delivery. Loop form.",
        "tags": ("[Verse 1: Fingerpicked]", "[Chorus: Gang, Open]", "[Bridge: Quiet]"),
    },
}


def _pct_pair(pair: list[tuple[str, int]]) -> str:
    return ", ".join(f"{n} ({w}%)" for n, w in pair)


def _style(theme: dict, title: str) -> str:
    g = _pct_pair(theme["genre"])
    gender, rng, delivery = theme["vocal"]
    tempo, bpm, sig = theme["tempo"]
    return (
        f"{g}. {tempo} feel, {bpm} BPM, {sig}. {delivery}. {gender} lead"
        + (f", {rng}" if rng != "Unspecified" else "")
        + f". {theme['style_extra']}. Distinct sections, studio production, no generic wash."
    )


def _lyrics(theme: dict, title: str, stagger: bool, breaks: bool, call: bool) -> str:
    v1, v2 = theme["v"][:4], theme["v"][4:8] or theme["v"][:4]
    chorus = theme["c"]
    pre = theme["pre"]
    br = theme["br"][:2] if len(theme["br"]) >= 2 else theme["br"]
    t1, t2, t3 = theme["tags"][0], theme["tags"][1], theme["tags"][-1]
    tempo = theme["tempo"][0]
    adlib = " (say it back)" if call else ""
    blank = [""] if breaks else []
    v2_tag = "[Verse 2: Staggered meter, alternate feet]" if stagger else "[Verse 2]"
    parts: list[str] = [
        "[Start]",
        f"[Tempo: {tempo}]",
        f"[Intro: {theme['style_extra'].split(',')[0]}]",
        *blank,
        t1,
        *v1,
        *blank,
        "[Pre-Chorus]",
        *pre,
        *blank,
        t2,
        *[line + adlib for line in chorus],
        *blank,
        v2_tag,
        *v2,
        *blank,
        t3,
        *br,
        *blank,
        "[Chorus, Final, Harmonized]",
        *chorus,
        "[End]",
    ]
    return "\n".join(parts)


def format_example(brief: dict, style: str, lyrics: str) -> str:
    """Legacy sandwich dump — kept for extract seeds, not used as LM training text."""
    lines = [BOS_BRIEF]
    for k, v in brief.items():
        lines.append(f"{k.upper()}: {v}")
    lines += [BOS_SHEET, f"STYLE: {style}", "LYRICS:", lyrics.strip(), EOS]
    return "\n".join(lines)


def format_lyric_block(title: str, idea: str, kind: str, lines: list[str]) -> tuple[str, str]:
    header = f"Title: {title}\nIdea: {idea}\n{kind}:\n"
    body = "\n".join(ln.strip() for ln in lines if ln and ln.strip())
    text = header + body + "\n<|endoftext|>"
    return text, header


def parse_sheet(text: str) -> dict | None:
    """Pull STYLE / LYRICS out of a model sample (prompt + continuation)."""
    cleaned = (
        (text or "")
        .replace("<|endoftext|>", "")
        .replace(EOS, "")
    )
    title_m = re.search(r"^TITLE:\s*(.+)$", cleaned, re.M) or re.search(r"^Title:\s*(.+)$", cleaned, re.M)
    title = title_m.group(1).strip() if title_m else "Untitled"

    body = cleaned
    if BOS_SHEET in body:
        body = body.split(BOS_SHEET, 1)[1]
    elif "STYLE:" in body:
        body = body[body.find("STYLE:") :]
    elif "[Start]" in body:
        body = body[body.find("[Start]") :]
    body = body.strip()
    if not body:
        return None

    style = ""
    lyrics = body
    if body.startswith("STYLE:") or "\nSTYLE:" in body:
        rest = body.split("STYLE:", 1)[1] if "STYLE:" in body else body
        split = re.split(r"\nLYRICS:\s*", rest, maxsplit=1)
        if len(split) == 2:
            style, lyrics = split[0], split[1]
        elif "[Start]" in rest:
            style, _, tail = rest.partition("[Start]")
            lyrics = "[Start]" + tail
        else:
            style, lyrics = rest, ""
    elif "[Start]" in body:
        lyrics = body[body.find("[Start]") :]

    style = style.strip()
    lyrics = lyrics.strip()
    if not style and not lyrics:
        return None
    return {"title": title, "stylePrompt": style, "lyrics": lyrics}


def _brief_from_theme(theme: dict, title: str, idea: str, dna: str) -> dict:
    g = theme["genre"]
    gender, rng, delivery = theme["vocal"]
    tempo, bpm, sig = theme["tempo"]
    return {
        "title": title,
        "pov": random.choice(["first", "second", "third"]),
        "genre": _pct_pair(g),
        "vocal": f"{gender} {rng}",
        "tempo": f"{tempo} {bpm} {sig}",
        "form": theme["form"],
        "rhyme": theme["rhyme"],
        "idea": idea,
    }


def generate_seed_extracts() -> list[dict]:
    rng = random.Random(14)
    rows = []
    for key, theme in THEMES.items():
        for i in range(3):
            title = theme["titles"][i % len(theme["titles"])]
            lyrics = _lyrics(theme, title, stagger=True, breaks=True, call=bool(theme.get("call")))
            ext = extract_song(lyrics, title=title, source=f"seed:{key}")
            ext["theme"] = key
            ext["dna"] = theme["dna"]
            rows.append(ext)
    rng.shuffle(rows)
    return rows


def _section_slices(theme: dict) -> list[tuple[str, list[str]]]:
    v = list(theme["v"])
    slices: list[tuple[str, list[str]]] = []
    for start in range(0, max(1, len(v) - 3), 2):
        chunk = v[start : start + 4]
        if len(chunk) >= 3:
            slices.append(("Verse", chunk))
    c = list(theme["c"])
    if len(c) >= 2:
        slices.append(("Chorus", c[:4]))
        if len(c) > 4:
            slices.append(("Chorus", c[2:6] if len(c) >= 6 else c[-4:]))
    pre = list(theme["pre"])
    if pre:
        slices.append(("Pre-Chorus", pre[:2] if len(pre) >= 2 else pre))
    br = list(theme["br"])
    if br:
        slices.append(("Bridge", br[:2] if len(br) >= 2 else br))
    return slices


def generate_corpus(n: int = 720) -> list[dict]:
    """Lyric-verse examples for causal LM SFT. Original lines only."""
    rng = random.Random(2026)
    keys = list(THEMES.keys())
    rows: list[dict] = []
    user_rows = _load_jsonl(USER_EXTRACTS)
    i = 0
    while len(rows) < n:
        key = keys[i % len(keys)]
        theme = THEMES[key]
        title = rng.choice(theme["titles"])
        idea = rng.choice(theme["ideas"])
        if i % 5 == 0 and user_rows:
            u = user_rows[i % len(user_rows)]
            idea = u.get("idea") or idea
            title = u.get("title") or title
            sung = u.get("sung") or []
            if not sung and u.get("text"):
                sung = [
                    ln.strip()
                    for ln in u["text"].splitlines()
                    if ln.strip() and not ln.strip().startswith("[")
                ]
            if len(sung) >= 3:
                text, prompt = format_lyric_block(title, idea or "User extract", "Verse", sung[:4])
                rows.append({"text": text, "prompt": prompt, "theme": key, "title": title, "kind": "Verse"})
                i += 1
                continue
        slices = _section_slices(theme)
        kind, lines = slices[i % len(slices)]
        if rng.random() > 0.45:
            rot = rng.randint(0, max(0, len(lines) - 1))
            lines = lines[rot:] + lines[:rot]
        text, prompt = format_lyric_block(title, idea, kind, lines)
        rows.append({"text": text, "prompt": prompt, "theme": key, "title": title, "kind": kind})
        if rng.random() > 0.55:
            v = theme["v"][:4]
            c = theme["c"][:4]
            header = f"Title: {title}\nIdea: {idea}\n"
            body = "Verse:\n" + "\n".join(v) + "\nChorus:\n" + "\n".join(c)
            rows.append(
                {
                    "text": header + body + "\n<|endoftext|>",
                    "prompt": header + "Verse:\n",
                    "theme": key,
                    "title": title,
                    "kind": "song",
                }
            )
        i += 1
    return rows[:n]


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_all(n: int = 720) -> dict:
    seeds = generate_seed_extracts()
    write_jsonl(SEED_EXTRACTS, seeds)
    rows = generate_corpus(n)
    write_jsonl(CORPUS_JSONL, rows)
    return {"extracts": len(seeds), "examples": len(rows), "corpus": str(CORPUS_JSONL)}


def lyric_prompt(composer: dict, kind: str = "Verse") -> str:
    title = composer.get("title") or "Untitled"
    idea = composer.get("idea") or "Invent a specific story that fits the pocket."
    return f"Title: {title}\nIdea: {idea}\n{kind}:\n"


def brief_from_composer(composer: dict, style_live: str = "", dna: str = "") -> str:
    """Prompt header the LM is trained to continue."""
    return lyric_prompt(composer, "Verse")
