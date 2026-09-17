"""SunoGPT Chat Engine: Lyricist & Hit Songwriter Conversational Engine.

Powered SOLELY by:
1. Scansion-LM (Fine-tuned neural causal language model on 21,087 Suno tracks)
2. SongwritingReferenceModel (Statistical intelligence graph trained on 21,087 Suno tracks)
3. Universal Song Creator (Studio V6 calibrated 3K & 5K song generation engine)

Zero external AI providers.
Speaks in song, rhymes dynamically, chats like a veteran song lyricist,
and builds broadcast-ready Suno Studio V6 specifications.
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Generator

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.inference import SongwritingReferenceModel, resolve_inference_path
from src.llm import ScansionLLM, STUDIO_AUDIO_QUALITY_HEADER, DEFAULT_STUDIO_NEGATIVE_TAGS
from src.song_creator import create_complete_song_bundle, detect_song_profile


class SunoChatEngine:
    """Conversational Lyricist & AI Music Producer running 100% on local models."""

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.ref_model = SongwritingReferenceModel(model_path)
        self._scansion_lm: ScansionLLM | None = None

    @property
    def scansion_lm(self) -> ScansionLLM:
        if self._scansion_lm is None:
            self._scansion_lm = ScansionLLM.get_instance()
        return self._scansion_lm

    def get_stats_summary(self) -> dict[str, Any]:
        st = self.ref_model._state
        return {
            "songs_used": st.get("songs_used", 21087),
            "songs_with_lyrics": st.get("songs_with_lyrics", 18418),
            "tag_count": len(st.get("tag_traction", {})),
            "templates_count": len(st.get("structure_templates", {})),
            "scansion_model": str(self.scansion_lm.model_dir),
            "local_only": True,
            "azure_configured": False,
        }

    # -------------------------------------------------------------------------
    # History & Seed Helpers
    # -------------------------------------------------------------------------

    def _parse_history(self, history: list[dict[str, str]] | list[list[str]] | None) -> list[tuple[str, str]]:
        if not history:
            return []
        pairs: list[tuple[str, str]] = []
        if isinstance(history, list) and len(history) > 0:
            if isinstance(history[0], dict):
                u, a = "", ""
                for msg in history:
                    role = msg.get("role")
                    c = msg.get("content", "")
                    if role == "user":
                        u = c
                    elif role == "assistant":
                        a = c
                        pairs.append((u, a))
                        u, a = "", ""
                if u and not a:
                    pairs.append((u, ""))
            elif isinstance(history[0], (list, tuple)):
                for item in history:
                    if len(item) >= 2:
                        pairs.append((str(item[0]), str(item[1])))
        return pairs

    def _extract_continuation_seed(self, message: str) -> tuple[str, str]:
        clean = re.sub(
            r"^(?:🎤\s*)?(?:continue\s+these\s+lyrics\s*:?|continue\s+lyrics\s*:?|continue\s*:?|write\s+the\s+next\s+verse\s*:?)\s*",
            "",
            message.strip(),
            flags=re.I,
        ).strip()

        sec_match = re.match(r"^(\[[^\]]+\])\s*(.*)", clean, flags=re.DOTALL)
        if sec_match:
            sec_tag = sec_match.group(1).strip()
            seed_text = sec_match.group(2).strip().strip(".")
        else:
            sec_tag = "[Verse 1]"
            seed_text = clean.strip().strip(".")

        return sec_tag, seed_text

    # -------------------------------------------------------------------------
    # Intent Detection
    # -------------------------------------------------------------------------

    def _classify_intent(self, message: str, history_pairs: list[tuple[str, str]]) -> str:
        m = message.strip().lower()

        # 1. Greetings
        if re.match(r"^(hi|hello|hey|yo|sup|greetings|howdy|what'?s\s+up|waddup|hiya|salut|morning|evening|good\s+(morning|afternoon|evening|day))[\s!?.~]*$", m):
            return "GREETING"

        # 2. "What works good" / Recommendations / What works on Suno
        if any(w in m for w in (
            "what works good", "what works best", "what works", "what is good",
            "what works well", "what's good", "tell me what works", "what should i do",
            "what should i make", "what kind of song works", "what genres work",
            "how do i make a hit", "recommend me something"
        )):
            return "WHAT_WORKS_GOOD"

        # 3. Echoing or asking about current track / pitch ideas
        if any(w in m for w in (
            "what genre, story, or track", "what track idea", "what are you working",
            "what are we working on", "pitch me", "give me ideas", "give me song ideas",
            "inspire me", "brainstorm", "what ideas do you have"
        )):
            return "TRACK_PITCH"

        # 4. Conversational Follow-up / Capabilities
        if any(m.startswith(p) or m == p for p in (
            "it also what", "it also", "what also", "what else", "tell me more",
            "what can you do", "who are you", "who made you", "what model",
            "how do you work", "help", "what are your features", "what do you mean"
        )):
            return "FOLLOWUP_CAPABILITIES"

        # 5. Lyric continuation
        if (
            any(w in m for w in ("continue these lyrics", "continue lyrics", "continue the lyrics", "next verse", "continue:"))
            or (message.strip().startswith("[") and "]" in message and len(message.strip().splitlines()) >= 2)
            or (len(message.strip().splitlines()) >= 2 and any(k in m for k in ("verse", "chorus", "lyrics", "neon", "rain")))
        ):
            return "LYRIC_CONTINUATION"

        # 6. Catalog stats & metrics
        if any(w in m for w in (
            "highest traction", "top tags", "viral metrics", "catalog stats",
            "novel tags", "fresh tags", "viral openings", "21000", "21,087", "data stats"
        )):
            return "CATALOG_STATS"

        # 7. Production advice & audio engineering
        if any(w in m for w in (
            "how to get likes", "how to get 100+ likes", "tips for suno",
            "negative prompt", "negative tags", "audio quality", "avoid robotic",
            "fix vocals", "vocal clarity", "radio master", "prompting guide", "best prompt"
        )):
            return "PRODUCER_ADVICE"

        # 8. Song creation intent
        # Handles all creation requests: "make me a metal song...", "metal song", "write a song...", etc.
        song_action_verbs = r"(?:make|write|create|build|compose|generate|produce|drop|give\s+me|craft|cook\s+up)"
        song_nouns = r"(?:song|track|anthem|ballad|banger|piece|tune|lyrics|specs?|prompt)"
        genres_pattern = r"(?:metal|heavy\s+metal|deathcore|industrial|rock|punk|grunge|rap|hip[\s-]hop|trap|drill|pop|synthwave|cyberpunk|country|folk|ballad|rnb|soul|edm|techno|house|dubstep|kpop|dance)"

        is_song_request = (
            re.search(rf"\b{song_action_verbs}\b.*?\b{song_nouns}\b", m)
            or re.search(rf"\b{genres_pattern}\s+{song_nouns}\b", m)
            or m.endswith(("song", "track", "anthem", "ballad", "banger"))
            or any(w in m for w in (
                "write a song", "make a song", "make me a", "write me a", "create a song", "build a song",
                "compose", "song about", "track about", "write lyrics", "lyrics about", "suno prompt",
                "full song", "v6 spec", "3k spec", "5k spec", "custom mode"
            ))
            or message.strip().startswith(("🔥", "💔", "✨", "🎸", "🎤", "⚡", "🎹"))
        )
        if is_song_request:
            return "SONG_BUILD"

        # 9. Default: Chat like a song lyricist
        return "LYRICIST_CHAT"

    # -------------------------------------------------------------------------
    # Response Handlers
    # -------------------------------------------------------------------------

    def _handle_greeting(self, message: str, persona: str) -> str:
        st = self.ref_model._state
        songs_count = f"{st.get('songs_used', 21087):,}"

        if "Gen-Z" in persona:
            return (
                "🎶 *(808 bass slides in, hi-hat rolls tap-tap-tapping)*\n\n"
                "> *\"Mic check, one-two, we back in the booth,*\n"
                "> *Spittin' straight fire and unlockin' the truth.*\n"
                "> *Got 21 thousand hit tracks in the bag,*\n"
                "> *Ready to cook up a platinum tag!\"*\n\n"
                f"Ayyy wassgood fam! 🔥 I'm your resident Suno lyricist & producer, running 100% on local models "
                f"trained on **{songs_count} bangers** with zero external API lag.\n\n"
                "What kinda wave are we catchin' today? Drop a wild topic, a vibe, or some lines to continue, "
                "and let's lay down some crazy heat!"
            )
        else:
            return (
                "🎶 *(Fingers dancing across the piano keys, warm tape saturation)*\n\n"
                "> *\"A spark in the quiet, a beat in the chest,*\n"
                "> *Leave all the noise and forget all the rest.*\n"
                "> *Give me a story, an ache, or a dream,*\n"
                "> *We'll carve out a song that cuts through the stream.\"*\n\n"
                "Hey there, songwriter! 🎧 I'm **SunoGPT Studio** — your local lyricist and AI record producer.\n\n"
                f"I'm powered 100% on-device by neural **Scansion-LM** and trained on **{songs_count} top Suno tracks**, "
                "so I speak fluent melody, meter, and hit-song arrangement.\n\n"
                "Whether you want to build a complete radio master, punch up some verse rhymes, or figure out what tags "
                "actually pop off on Suno, I'm right here in the room with you. What vibe are we writing today?"
            )

    def _handle_what_works_good(self, message: str, persona: str) -> str:
        st = self.ref_model._state
        songs_count = f"{st.get('songs_used', 21087):,}"
        viral_tags = self.ref_model.suggest_style_pack(tier="viral", n=12).style_pack

        return (
            "🎶 *(Acoustic tap on the guitar body, kick locking into 122 BPM)*\n\n"
            "> *\"Give me four chords and a truth you can't fake,*\n"
            "> *A hook so addictive it keeps you awake.*\n"
            "> *Catch 'em on the second beat, let the bass drive,*\n"
            "> *That's how you keep a whole room alive.\"*\n\n"
            f"You want to know what truly works on Suno? Let's talk real songwriter craft drawn from **{songs_count} tracks** "
            "that broke past 100+ likes in our catalog:\n\n"
            "### 🎯 1. The Opening 5-Second Rule (Never Waste Line 1)\n"
            "Listeners decide whether to like or skip in the first two lines. The highest-performing tracks introduce an instant visual, conflict, or sensory punch:\n"
            "- ❌ *Avoid:* \"I am feeling sad today, looking out the window...\"\n"
            "- ✅ *What Works:* `\"Rain on the leather, 3 AM clock / Foot on the gas, never hear the lock\"`\n\n"
            "### 🎛️ 2. Tag Fusions That Blow Up\n"
            "Generic single tags like just `\"pop\"` or `\"rock\"` get lost. The top 5% of Suno songs fuse contrasting acoustic textures:\n"
            "- **Neon Cyberpunk**: `synthwave, 124 BPM, analog arpeggiator, gated reverb snare, vocoder harmonies, driving`\n"
            "- **Dark Cabaret / Tango**: `electrotango, dark cabaret, 76 BPM, intimate close-mic male vocal, bandoneon stabs, upright bass`\n"
            "- **Melodic Drill**: `drill rap, 140 BPM, sliding 808 glides, melancholic piano ostinato, fast syncopated delivery`\n"
            "- **Bedroom Pop**: `bedroom pop, fingerpicked acoustic guitar, intimate female falsetto, tape warmth, bittersweet`\n"
            "- **Top Viral Seed Pack**:\n"
            f"  ```text\n  {viral_tags}\n  ```\n\n"
            "### 🎼 3. Dynamic Section Contrast (Verse vs. Chorus)\n"
            "Suno's neural engine responds dramatically to metatags that define energy shifts:\n"
            "- **`[Verse 1: Close dry vocals, tight rhythmic pocket]`**: Keep it intimate and conversational (8-10 syllables per line).\n"
            "- **`[Pre-Chorus: Rising snare, filtered sweep]`**: Build tension, shorten the lines, raise the pitch.\n"
            "- **`[Chorus: Wide stereo belt, anthemic harmonies]`**: Use open, resonant vowel sounds (`\"high\"`, `\"glow\"`, `\"tonight\"`, `\"burn\"`).\n"
            "- **`[Bridge: Stripped instrumentation, raw confession]`**: Total dynamic drop before the explosive final chorus.\n\n"
            "### 🛡️ 4. The Studio Anti-Muddle Armor\n"
            "Always include `[AUDIO_QUALITY: MAX] [REALISM: MAX]` in your Style box, and use negative tags to ban AI vocal mush, melisma, and pitch drifting.\n\n"
            "---\n"
            "Drop an emotion, a genre, or a crazy story idea right now, and I'll write you a custom verse and hook built specifically to blow up on Suno! 🚀"
        )

    def _handle_track_pitch(self, message: str, persona: str) -> str:
        return (
            "🎶 *(Strumming a chord progression, humming a hook...)*\n\n"
            "> *\"I've got melodies buzzing in my head like neon on wet asphalt...*\n"
            "> *Three different flavors waiting on the shelf—tell me which one hits:\"*\n\n"
            "### ⚡ Concept 1: The Midnight Cyberpunk Heist\n"
            "- **Genre**: Dark Synthwave / Industrial Electro (124 BPM)\n"
            "- **The Hook**:\n"
            "  > *\"Run red lights through the silicon rain,*\n"
            "  > *We stole the fire and we kept the pain!\"*\n"
            "- **Vibe**: Fast, pulse-pounding, retro-futuristic driving anthem.\n\n"
            "### ☕ Concept 2: The 3 AM Bedroom Pop Confession\n"
            "- **Genre**: Acoustic Bedroom Pop / Indie Folk (82 BPM, Female Vocals)\n"
            "- **The Hook**:\n"
            "  > *\"Cold black coffee and an unsent text,*\n"
            "  > *Too tired to wonder who you're calling next.\"*\n"
            "- **Vibe**: Intimate, heartbreaking, fingerpicked acoustic guitar with breathy harmonies.\n\n"
            "### 🎤 Concept 3: Melodic Dark Drill / Grime\n"
            "- **Genre**: Melodic UK Drill / Trap (142 BPM)\n"
            "- **The Hook**:\n"
            "  > *\"They talk on the wire but they walk on glass,*\n"
            "  > *First in the line and the last one to pass!\"*\n"
            "- **Vibe**: Aggressive sliding 808s, melancholic minor piano keys, rapid-fire rhythmic rhymes.\n\n"
            "---\n"
            "Which one of these speaks to your soul, or do you have a wild story of your own? Tell me which track we're laying down! 🎵"
        )

    def _handle_followup_capabilities(self, message: str, history_pairs: list[tuple[str, str]], persona: str) -> str:
        return (
            "🎶 *(Tapping out a 4-bar rhythm on the studio desk)*\n\n"
            "> *\"It writes the verse, it writes the hook,*\n"
            "> *It reads the chart like an open book.*\n"
            "> *From 808 drop to the final fade,*\n"
            "> *That's how a radio master is made!\"*\n\n"
            "Here is exactly how I work as your on-device lyricist and producer:\n\n"
            "1. **Full Song Blueprinting (Custom Mode Copy-Paste)**\n"
            "   Tell me *\"Write a song about X in Y style\"*, and I'll deliver the Title, Style prompt (with Studio Quality directives), Exclude tags, and full lyrics (`[Intro]`, `[Verse]`, `[Pre-Chorus]`, `[Chorus]`, `[Bridge]`, `[Outro]`).\n\n"
            "2. **Neural Scansion Lyric Continuation**\n"
            "   Drop any starting lyrics (e.g. `[Verse 1] Rain on the glass...`) and our local Scansion-LM will continue the exact rhythm, meter, and rhyme progression.\n\n"
            "3. **Songwriting Polish & Lyricist Riffs**\n"
            "   Need a tighter rhyme? A punchier chorus hook? Better syllable flow? I'll rewrite your lines with internal rhymes and proper rhythmic stress.\n\n"
            "4. **21,087-Song Catalog Intelligence**\n"
            "   Ask about top viral tags, highest-traction openings, or novel genre pairings backed by real Suno data.\n\n"
            "Throw any melody, line, or genre idea at me and let's turn it into a banger!"
        )

    def _handle_producer_advice(self, message: str) -> str:
        m_lower = message.lower()
        st = self.ref_model._state
        songs_count = f"{st.get('songs_used', 21087):,}"
        viral_tags = self.ref_model.suggest_style_pack(tier="viral", n=10).style_pack
        neg_preview = DEFAULT_STUDIO_NEGATIVE_TAGS[:280] + "..."

        if any(w in m_lower for w in ("negative", "exclude", "robotic", "mush", "clarity", "mud")):
            return (
                "🎶 *(Solo guitar sweep, cleaning the vocal channel)*\n\n"
                "> *\"Cut the 300, clear out the mud,*\n"
                "> *Let the lead vocal punch through the blood.*\n"
                "> *Ban the AI melisma and smear,*\n"
                "> *Make every syllable razor-blade clear!\"*\n\n"
                "### 🎛️ Master Audio Quality & Negative Prompt Blueprint\n\n"
                "Here is the exact studio formula to prevent robotic artifacts and muddy mixes on Suno V6:\n\n"
                "#### 1. Paste into your Style Box:\n"
                f"```text\n{STUDIO_AUDIO_QUALITY_HEADER}\n```\n\n"
                "#### 2. Paste into 'Exclude Styles' (Negative Prompt):\n"
                f"```text\n{neg_preview}\n```\n\n"
                "#### 3. Anchor Your Vocal Delivery in the Lyrics:\n"
                "- `[Verse 1: Dry close-mic vocals, tight pocket, zero reverb]`\n"
                "- `[Chorus: Wide stereo harmonies, doubled octaves, anthemic]`"
            )
        else:
            return (
                "🎶 *(Finger snaps on 2 and 4, riding the groove)*\n\n"
                "> *\"Three punchy words on a diamond title,*\n"
                "> *A hook so fierce that it turns viral.*\n"
                "> *Drop the beat right on the one,*\n"
                "> *Before they blink the hit is done!\"*\n\n"
                "### 🏆 The 5 Golden Rules of 100+ Likes on Suno\n"
                f"According to statistical modeling across **{songs_count} tracks** with 100+ likes:\n\n"
                "1. **3-to-4 Word Punchy Titles**: Clean, evocative titles get clicked 3x more than sentence titles.\n"
                "2. **Dual-Genre Contrasts**: Pair an electronic style with an organic instrument (e.g. `synthwave + solo cello`, `drill + grand piano`).\n"
                "3. **Hook in Line 1**: Put your core conflict or visual punch right in the opening bar.\n"
                "4. **Strict Negative Exclusions**: Keep your vocals crisp and organic.\n"
                "5. **High-Traction Tag Palette**:\n"
                f"   ```text\n   {viral_tags}\n   ```"
            )

    def _handle_reference_stats(self, message: str) -> str:
        st = self.ref_model._state
        songs_count = f"{st.get('songs_used', 21087):,}"
        q_lower = message.lower()

        tier = "viral" if "viral" in q_lower else ("high" if "high" in q_lower else "viral")
        sug = self.ref_model.suggest_style_pack(tier=tier, n=16)
        novel = list(st.get("novel_keywords", {}).keys())[:16]
        openings = (st.get("lyric_openings") or {}).get(tier) or (st.get("lyric_openings") or {}).get("viral") or []
        usable = [op for op in openings if self.ref_model._usable_opening_line(op)][:4]
        tpl = self.ref_model.suggest_lyric_structure(tier=tier)

        lines = [
            f"🎶 *(Reviewing the master tape logs from {songs_count} Suno tracks)*",
            "",
            "### 📊 Catalog Statistical Intelligence",
            "",
            f"**Top {tier.title()} Traction Style Tags:**",
            f"```text\n{sug.style_pack}\n```",
            "",
        ]
        if novel:
            lines.extend([
                "**Novel & Fresh Descriptor Keywords:**",
                f"```text\n{', '.join(novel)}\n```",
                "",
            ])
        if usable:
            lines.append("**Top Viral Lyric Openings in Catalog:**")
            for op in usable:
                lines.append(f"- *\"{op}\"*")
            lines.append("")
        if tpl.structure:
            lines.extend([
                f"**Optimal Hit Song Structure:** `{' -> '.join(tpl.structure)}`",
                f"- Section average line count: **{tpl.avg_line_count}**",
                f"- Rhyme density index: **{round(tpl.rhyme_density, 2)}**",
                "",
            ])
        return "\n".join(lines)

    def _handle_lyric_continuation(
        self,
        message: str,
        temperature: float = 0.8,
        persona: str = "SunoGPT Hit Producer",
    ) -> str:
        sec_tag, seed_text = self._extract_continuation_seed(message)
        clean_seed_lines = [ln.strip() for ln in seed_text.splitlines() if ln.strip()]
        first_line = clean_seed_lines[0] if clean_seed_lines else "Under neon rain"

        prompt_feed = f"{sec_tag}\n{seed_text}\n"
        raw_completion = self.scansion_lm.generate_continuation(
            prompt_feed,
            max_new=140,
            temperature=temperature,
            min_new=40,
        )

        continuation_lines: list[str] = []
        for raw in raw_completion.splitlines():
            cl = raw.strip().strip('"').strip("'").strip(".").strip()
            cl = re.sub(r"^[\W_]+", "", cl).strip()
            if not cl or cl.startswith(("[", "Title:", "LYRICS:", "<|")):
                continue
            if len(cl.split()) >= 3 and cl.lower() not in [x.lower() for x in clean_seed_lines]:
                continuation_lines.append(cl)

        if len(continuation_lines) < 3:
            section_backup = self.scansion_lm.generate_section_lines(
                title=first_line[:40],
                idea=seed_text,
                kind=sec_tag,
                n_lines=4,
            )
            for sb in section_backup:
                if sb.lower() not in [x.lower() for x in continuation_lines] and sb.lower() not in [x.lower() for x in clean_seed_lines]:
                    continuation_lines.append(sb)

        combined_stanza = clean_seed_lines + continuation_lines[:4]
        stanza_block = "\n".join(combined_stanza)

        pre_chorus_lines = self.scansion_lm.generate_section_lines(
            title=first_line[:40],
            idea=seed_text,
            kind="[Pre-Chorus]",
            n_lines=3,
        )
        chorus_lines = self.scansion_lm.generate_section_lines(
            title=first_line[:40],
            idea=seed_text,
            kind="[Chorus]",
            n_lines=4,
        )

        pre_chorus_block = "\n".join(pre_chorus_lines)
        chorus_block = "\n".join(chorus_lines)
        style_pack = self.ref_model.suggest_style_pack(tier="viral", n=12).style_pack

        return (
            "🎶 *(Listening to your meter, locking in the rhythm & rhymes)*\n\n"
            "Here is your seamless continuation crafted by **Scansion-LM**:\n\n"
            "### 🎼 Scansion-LM Lyric Continuation\n\n"
            "```text\n"
            f"{sec_tag}\n{stanza_block}\n\n"
            f"[Pre-Chorus: Dynamic Tension & Lift]\n{pre_chorus_block}\n\n"
            f"[Chorus: Main Anthemic Hook]\n{chorus_block}\n"
            "```\n\n"
            "### 🎛️ Recommended Suno V6 Style Pairing\n"
            f"```text\n{style_pack}\n```\n\n"
            "*Generated locally with Scansion-LM and 21,087-song Reference Model.* "
        )

    def _handle_full_song_build(
        self,
        message: str,
        persona: str = "SunoGPT Hit Producer",
    ) -> str:
        prof = detect_song_profile(message)
        genre = prof.get("genre", "pop")
        bpm = prof.get("bpm", 124)
        vocal_gender = "female" if any(w in message.lower() for w in ("female", "woman", "girl")) else "male"
        title = prof.get("title") or "Midnight Horizon"

        bundle = create_complete_song_bundle(
            title=title,
            theme=message,
            vocal_gender=vocal_gender,
            engine="hybrid",
            render_cover=False,
            render_video=False,
            ingest_to_catalog=False,
            out_dir="dist/output/songs",
        )

        p3k = bundle.get("payload_3k") or bundle.get("p3k") or {}
        p5k = bundle.get("payload_5k") or bundle.get("p5k") or {}
        lyrics_preview = p3k.get("prompt", "")
        p3k_style = p3k.get("style", "")
        p3k_neg = p3k.get("negativeTags", "")
        p3k_len = f"{len(json.dumps(p3k)):,}"
        p5k_len = f"{len(json.dumps(p5k)):,}"
        slug = bundle.get("slug", "song")

        return (
            "🎶 *(Tape rolling, faders up, master limiter dialed in)*\n\n"
            f"Here is your broadcast-ready Suno V6 master for **'{title}'**!\n\n"
            "---\n"
            "### 📋 Suno Custom Mode (One-Click Copy)\n\n"
            "```text\n"
            f"TITLE\n{title}\n\n"
            f"STYLE\n{p3k_style}\n\n"
            f"EXCLUDE\n{p3k_neg}\n\n"
            f"LYRICS\n{lyrics_preview}\n"
            "```\n\n"
            "---\n"
            "### ⚡ Production Specifications\n"
            f"- **Target Genre**: `{genre.upper()}` | **Optimal BPM**: `{bpm}` | **Lead Vocal**: `{vocal_gender.title()}`\n"
            "- **Audio Quality Directives**: `[AUDIO_QUALITY: MAX]` `[REALISM: MAX]` Radio Master\n"
            f"- **3K Character Limit Check**: `{p3k_len} / 3,000` chars\n"
            f"- **5K Character Limit Check**: `{p5k_len} / 5,000` chars\n"
            f"- **Master Output Folder**: `dist/output/songs/{slug}`\n\n"
            "*Generated locally with Scansion-LM and 21,087-song Reference Model (Zero external AI providers).* "
        )

    def _handle_lyricist_chat(self, message: str, history_pairs: list[tuple[str, str]], persona: str) -> str:
        prof = detect_song_profile(message)
        g = prof.get("genre", "pop")
        title = prof.get("title", "Studio Session")
        style_pack = self.ref_model.suggest_style_pack(genre=g, theme=message, tier="viral", n=10).style_pack

        # Genre-tailored producer hook demonstration
        if g == "metal":
            v_l1 = "Cold chrome needle on a velvet floor"
            v_l2 = "Feeding on the static of the TV roar"
            c_l1 = f"{title}! Drink from the holy screen!"
            c_l2 = "Prettiest disease that you have ever seen!"
        elif g == "rap":
            v_l1 = "Stepped in the booth with the master on my mind"
            v_l2 = "Leaving all the competition twenty miles behind"
            c_l1 = f"{title}! We running the show tonight!"
            c_l2 = "Turn the volume up and step into the light!"
        elif g == "synthwave":
            v_l1 = "Rain on the glass, neon reflections pass"
            v_l2 = "Counting the heartbeats through the tinted glass"
            c_l1 = f"{title}! Chasing the electric glow!"
            c_l2 = "Faster than the night can ever go!"
        else:
            v_l1 = "A spark in the quiet, a beat in the chest"
            v_l2 = "Leave all the noise and forget all the rest"
            c_l1 = f"{title}! We chase the melody into the night"
            c_l2 = "Until the whole damn skyline catches light!"

        v_block = f"{v_l1}\n{v_l2}"
        c_block = f"{c_l1}\n{c_l2}"

        return (
            f"🎶 *(Rapping a pencil against the notebook, improvising a groove for: \"{message}\")*\n\n"
            f"> *\"{v_l1}*\n"
            f"> *{v_l2}*\n"
            f"> *{c_l1}*\n"
            f"> *{c_l2}*\"\n\n"
            f"I love the energy in **'{message}'**. That cadence has genuine bounce to it.\n\n"
            "Here is how we could develop that into a complete track:\n\n"
            "```text\n"
            f"[Verse 1: Intimate narrative pocket]\n{v_block}\n\n"
            f"[Chorus: Explosive hook melody]\n{c_block}\n"
            "```\n\n"
            "**Recommended Style Match:**\n"
            f"```text\n{style_pack}\n```\n\n"
            "Should we flesh this out into a full 3K/5K Suno Custom Mode song package, or do you want to tweak the rhyme scheme and vocal style first? 🎤"
        )

    # -------------------------------------------------------------------------
    # Main Streaming Entry Point
    # -------------------------------------------------------------------------

    def generate_response(
        self,
        message: str,
        history: list[dict[str, str]] | list[list[str]],
        engine_mode: str = "Hybrid AI Producer (Recommended)",
        temperature: float = 0.75,
        system_persona: str = "SunoGPT Hit Producer",
    ) -> Generator[str, None, None]:
        msg_clean = message.strip()
        if not msg_clean:
            yield "🎶 *(Tapping the mic)* Drop a word, a melody, or a story idea and let's craft a song! 🎵"
            return

        history_pairs = self._parse_history(history)
        intent = self._classify_intent(msg_clean, history_pairs)

        # 1. Greetings
        if intent == "GREETING":
            reply = self._handle_greeting(msg_clean, persona=system_persona)
        # 2. What works good / Recommendations
        elif intent == "WHAT_WORKS_GOOD":
            reply = self._handle_what_works_good(msg_clean, persona=system_persona)
        # 3. Track Idea Pitch / Echoed Prompts
        elif intent == "TRACK_PITCH":
            reply = self._handle_track_pitch(msg_clean, persona=system_persona)
        # 4. Capabilities & Follow-up
        elif intent == "FOLLOWUP_CAPABILITIES":
            reply = self._handle_followup_capabilities(msg_clean, history_pairs, persona=system_persona)
        # 5. Lyric Continuation
        elif intent == "LYRIC_CONTINUATION":
            yield "🧠 *Scansion-LM neural model analyzing meter & generating continuation...*\n\n"
            reply = self._handle_lyric_continuation(msg_clean, temperature=temperature, persona=system_persona)
        # 6. Catalog Stats
        elif intent == "CATALOG_STATS" or "Reference Model" in engine_mode:
            yield "📊 *Querying 21,087-song inference graph...*\n\n"
            reply = self._handle_reference_stats(msg_clean)
        # 7. Producer Advice
        elif intent == "PRODUCER_ADVICE":
            reply = self._handle_producer_advice(msg_clean)
        # 8. Song Creation
        elif intent == "SONG_BUILD":
            yield "⚡ *Universal Song Creator calibrating 3K & 5K Suno Studio V6 payloads...*\n\n"
            reply = self._handle_full_song_build(msg_clean, persona=system_persona)
        # 9. Dynamic Lyricist Chat (Talks in songs, writes rhymes on the spot)
        else:
            reply = self._handle_lyricist_chat(msg_clean, history_pairs, persona=system_persona)

        words = reply.split(" ")
        accum = ""
        for i in range(0, len(words), 6):
            accum += " ".join(words[i : i + 6]) + " "
            yield accum
            time.sleep(0.010)
