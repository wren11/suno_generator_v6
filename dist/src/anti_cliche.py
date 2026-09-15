"""Anti-AI Songwriting Cliché Engine & Banned Vocabulary Purger.

Eliminates plastic AI songwriting clichés, dead giveaways, and hallucinations
(e.g., 'neon', 'tapestry', 'echoes', 'shadows', 'whispers', 'ignite', 'labyrinth', etc.)
ensuring authentic, visceral, grounded human lyrics and production directives.
"""

from __future__ import annotations

import re
from typing import Tuple, List

# Primary set of banned AI songwriting words and stems (case-insensitive word boundary)
BANNED_AI_WORDS: set[str] = {
    "neon",
    "tapestry",
    "tapestries",
    "echoes",
    "echoing",
    "echo",
    "whispers",
    "whispering",
    "whisper",
    "ignite",
    "ignites",
    "igniting",
    "labyrinth",
    "beacon",
    "beacons",
    "abyss",
    "ethereal",
    "celestial",
    "kaleidoscope",
    "kaleidoscopic",
    "cacophony",
    "intertwined",
    "intertwine",
    "ember",
    "embers",
    "ephemeral",
    "unfurl",
    "unfurls",
    "unfurling",
    "unveil",
    "unveils",
    "unveiling",
    "nexus",
    "testament",
    "resonate",
    "resonates",
    "resonating",
    "resonance",
    "uncharted",
    "illuminate",
    "illuminates",
    "illuminating",
    "illumine",
    "delve",
    "delves",
    "delving",
    "chrysalis",
    "transcend",
    "transcends",
    "transcending",
    "serenade",
}

# Negative tag injection chunk for Suno Studio V6 negative prompt
AI_CLICHE_NEGATIVE_TAGS = (
    "NEON, TAPESTRY, ECHOES, SHADOWS, WHISPERS, IGNITE, LABYRINTH, "
    "BEACON, ABYSS, ETHEREAL, CELESTIAL, KALEIDOSCOPE, MIDNIGHT HAZE, "
    "SHATTERED DREAMS, TESTAMENT, TRANSCEND, VAGUE AI POETRY, AI CLICHES"
)

# Ordered context-aware regex patterns for replacements
BANNED_AI_REPLACEMENTS: list[tuple[str, str]] = [
    # 1. 'Neon' (The #1 AI giveaway)
    (r"(?i)\bneon\s+lights?\b", "streetlights"),
    (r"(?i)\bneon\s+glow\b", "amber glow"),
    (r"(?i)\bneon\s+fire\b", "white-hot fire"),
    (r"(?i)\bneon\s+signs?\b", "highway signs"),
    (r"(?i)\bneon\s+rain\b", "acid rain"),
    (r"(?i)\bneon\s+streets?\b", "wet asphalt"),
    (r"(?i)\bneon\s+city\b", "concrete city"),
    (r"(?i)\bneon\s+blue\b", "cobalt blue"),
    (r"(?i)\bneon\s+sky\b", "smoky sky"),
    (r"(?i)\bneon\b", "chrome"),

    # 2. 'Tapestry'
    (r"(?i)\btapestry\s+of\b", "history of"),
    (r"(?i)\btapestries\b", "histories"),
    (r"(?i)\btapestry\b", "chronicle"),

    # 3. 'Echoes'
    (r"(?i)\bechoes\s+of\s+the\b", "rumble of the"),
    (r"(?i)\bechoes\s+of\b", "traces of"),
    (r"(?i)\bfading\s+echoes\b", "fading feedback"),
    (r"(?i)\bechoes\b", "reverb"),
    (r"(?i)\bechoing\b", "ringing"),
    (r"(?i)\becho\b", "reverb"),

    # 4. 'Shadows'
    (r"(?i)\bshadows\s+dance\b", "flickers play"),
    (r"(?i)\bshadows\s+fall\b", "night falls"),
    (r"(?i)\boutrunning\s+shadows\b", "outrunning headlights"),
    (r"(?i)\bshadows\s+of\s+the\b", "silhouettes of the"),
    (r"(?i)\bshadows\b", "silhouettes"),
    (r"(?i)\bshadowy\b", "darkened"),
    (r"(?i)\bshadow\b", "silhouette"),

    # 5. 'Whispers'
    (r"(?i)\bwhispers\s+in\s+the\s+dark\b", "murmurs in the dark"),
    (r"(?i)\bwhispers\s+in\s+the\s+wind\b", "rumors in the wind"),
    (r"(?i)\bwhispers\b", "murmurs"),
    (r"(?i)\bwhispering\b", "murmuring"),
    (r"(?i)\bwhisper\b", "murmur"),

    # 6. 'Ignite'
    (r"(?i)\bignite\s+the\s+flame\b", "strike the match"),
    (r"(?i)\bignite\s+the\s+night\b", "blow up the night"),
    (r"(?i)\bignite\s+the\s+spark\b", "kick start the spark"),
    (r"(?i)\bignites?\b", "triggers"),
    (r"(?i)\bignite\b", "trigger"),
    (r"(?i)\bigniting\b", "triggering"),

    # 7. 'Labyrinth'
    (r"(?i)\blabyrinth\s+of\b", "concrete maze of"),
    (r"(?i)\blabyrinth\b", "maze"),

    # 8. 'Beacon'
    (r"(?i)\bbeacon\s+of\s+hope\b", "searchlight"),
    (r"(?i)\bbeacons?\b", "searchlights"),
    (r"(?i)\bbeacon\b", "flare"),

    # 9. 'Abyss'
    (r"(?i)\binto\s+the\s+abyss\b", "into the drop"),
    (r"(?i)\babyss\b", "crater"),

    # 10. 'Ethereal' & 'Celestial'
    (r"(?i)\bethereal\s+glow\b", "ghostly glow"),
    (r"(?i)\bethereal\b", "spectral"),
    (r"(?i)\bcelestial\b", "midnight"),

    # 11. 'Kaleidoscope' & 'Cacophony'
    (r"(?i)\bkaleidoscope\s+of\b", "wild shift of"),
    (r"(?i)\bkaleidoscopic\b", "shifting"),
    (r"(?i)\bkaleidoscope\b", "prism"),
    (r"(?i)\bcacophony\s+of\b", "blaring roar of"),
    (r"(?i)\bcacophony\b", "racket"),

    # 12. 'Intertwined' & 'Embers'
    (r"(?i)\bintertwined\b", "locked tight"),
    (r"(?i)\bintertwine\b", "lock together"),
    (r"(?i)\bglowing\s+embers\b", "glowing coals"),
    (r"(?i)\bembers?\b", "coals"),
    (r"(?i)\bember\b", "coal"),

    # 13. 'Ephemeral', 'Unfurl', 'Unveil', 'Nexus'
    (r"(?i)\bephemeral\b", "temporary"),
    (r"(?i)\bunfurls?\b", "opens"),
    (r"(?i)\bunfurling\b", "opening"),
    (r"(?i)\bunveils?\b", "reveals"),
    (r"(?i)\bunveiling\b", "revealing"),
    (r"(?i)\bnexus\b", "crossroad"),

    # 14. Complex AI clichés
    (r"(?i)\bshattered\s+dreams\b", "wrecked plans"),
    (r"(?i)\bshattered\b", "smashed"),
    (r"(?i)\bsilent\s+screams\b", "clenched-jaw panic"),
    (r"(?i)\bmidnight\s+haze\b", "midnight fog"),
    (r"(?i)\bdigital\s+haze\b", "monitor glare"),
    (r"(?i)\bpurple\s+haze\b", "violet smog"),
    (r"(?i)\bpurple\s+rays\b", "halogen glare"),
    (r"(?i)\bdanc(ing|e)\s+in\s+the\s+rain\b", "standing in the pouring rain"),
    (r"(?i)\b(two\s+)?hearts?\s+beat(ing)?\s+as\s+one\b", "locked in the identical pulse"),
    (r"(?i)\btestament\s+to\b", "living proof of"),
    (r"(?i)\btestament\b", "proof"),
    (r"(?i)\bresonates?\b", "rattles"),
    (r"(?i)\bresonating\b", "rattling"),
    (r"(?i)\bresonance\b", "vibration"),
    (r"(?i)\buncharted\s+waters\b", "rough seas"),
    (r"(?i)\buncharted\b", "unmapped"),
    (r"(?i)\billuminat(es?|ing|ed)\b", "lights up"),
    (r"(?i)\billumine\b", "light up"),
    (r"(?i)\bsymphony\s+of\b", "chorus of"),
    (r"(?i)\bdelv(es?|ing)\s+into\b", "digs into"),
    (r"(?i)\bdelve\b", "dig"),
    (r"(?i)\brealm\s+of\b", "world of"),
    (r"(?i)\brealms\b", "districts"),
    (r"(?i)\brealm\b", "turf"),
    (r"(?i)\bchrysalis\b", "armor"),
    (r"(?i)\btranscend(s|ing|ed)?\b", "break through"),
    (r"(?i)\bboundless\b", "endless"),
    (r"(?i)\bfleeting\b", "passing"),
    (r"(?i)\bserenade\b", "ballad"),
]

_BANNED_SCANNER_REGEX = re.compile(
    r"\b(" + "|".join(sorted(re.escape(w) for w in BANNED_AI_WORDS)) + r")\b",
    re.IGNORECASE,
)


def purge_ai_cliches(text: str) -> str:
    """Sanitize lyrics, titles, and prompts by stripping and replacing banned AI clichés."""
    if not text:
        return ""

    result = text
    for pattern, replacement in BANNED_AI_REPLACEMENTS:
        result = re.sub(pattern, replacement, result)

    def _fallback_sub(m: re.Match) -> str:
        word = m.group(0).lower()
        if word == "neon":
            return "chrome"
        if "echo" in word:
            return "reverb"
        if "whisper" in word:
            return "murmur"
        if "ignit" in word:
            return "trigger"
        if word == "tapestry":
            return "story"
        if word == "labyrinth":
            return "maze"
        if word == "beacon":
            return "flare"
        if word == "abyss":
            return "crater"
        if word == "ethereal":
            return "ghostly"
        if word == "celestial":
            return "midnight"
        if "kaleidoscop" in word:
            return "prism"
        if word == "cacophony":
            return "racket"
        if "intertwin" in word:
            return "locked"
        if "ember" in word:
            return "coal"
        if word == "ephemeral":
            return "passing"
        if "unfurl" in word:
            return "open"
        if "unveil" in word:
            return "reveal"
        if word == "nexus":
            return "hub"
        if word == "testament":
            return "proof"
        if "resonat" in word or word == "resonance":
            return "rattle"
        if word == "uncharted":
            return "unmapped"
        if "illumin" in word:
            return "light up"
        if "delv" in word:
            return "dig"
        if word == "chrysalis":
            return "armor"
        if "transcend" in word:
            return "surpass"
        if word == "serenade":
            return "song"
        return "sound"

    result = _BANNED_SCANNER_REGEX.sub(_fallback_sub, result)
    return result


def validate_no_ai_cliches(text: str) -> Tuple[bool, List[str]]:
    """Scan text and return (True, []) if clean, or (False, [list of violations])."""
    if not text:
        return True, []
    matches = _BANNED_SCANNER_REGEX.findall(text)
    if matches:
        return False, sorted(list(set(m.lower() for m in matches)))
    return True, []


def clean_title_cliches(title: str) -> str:
    """Sanitize song titles of AI tropes (e.g., 'Neon Skyline' -> 'Chrome Skyline')."""
    if not title:
        return title
    t = purge_ai_cliches(title)
    words = [w.capitalize() if len(w) > 3 else w for w in t.split()]
    return " ".join(words)
