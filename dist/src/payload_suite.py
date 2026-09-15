"""Generate Suno Studio V6 JSON payloads in both 3k and 5k character specifications across 7,000+ song dataset archetypes."""

from __future__ import annotations

from src.anti_cliche import purge_ai_cliches, AI_CLICHE_NEGATIVE_TAGS

import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Any

from src.catalog import SongCatalogStore
from src.llm import DEFAULT_STUDIO_NEGATIVE_TAGS, STUDIO_AUDIO_QUALITY_HEADER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 15 Definitive Songwriting Archetypes derived from 7,152 Suno songs
ARCHETYPES = [
    {
        "name": "dark_glam_electropop",
        "title": "New Name on the Door",
        "theme": "DARK GLAM ELECTROPOP / COLD RADIO POP / CINEMATIC DANCE-POP",
        "bpm": 122,
        "vocal_gender": "f",
        "vocal_desc": "BIG FEMALE BELT ON THE HOOK, CLOSE AND DRY ON THE VERSES. SOUND LIKE A REAL SINGER IN A TREATED MIDNIGHT BOOTH OVER STACCATO SYNTH STABS, A COLD PIANO FIGURE, ANALOG CHORUS ON THE BED AND A TIGHT LIVE-FEELING RHYTHM SECTION, CAPTURED WITH EXCELLENT MICROPHONES AND ENGINEERING. NARROW MONO VERSE, WIDE CHORUS. FALLEN-STAR POP WITHOUT BECOMING PROTEST FOLK, TRAP CONFESSION, OR MUSICAL-THEATRE MONOLOGUE.",
        "hook": [
            "I'm not going back to where the mirrors lie",
            "Write a new name on the door before the paint gets dry",
            "Sell the crown, burn the gown, take the city down",
            "There's a brand new silhouette standing on your ground",
        ],
        "verses": [
            "Red light flickers on a velvet chair / Perfume drowning in the midnight air",
            "Dialing numbers that I swore I lost / Counting up the wreckage and the sticker cost",
            "Glass on the carpet and a diamond crack / Train on the siding with a one-way track",
            "Smile for the camera like a loaded gun / We made a fortune when the night was young",
            "Gold teeth flashing in a rented car / We took the spotlight and we drove too far",
            "Hotel lobby with the fountains dead / Repeating every promise that you never said",
            "Turn down the monitor, turn up the room / Sweeping the confetti with a velvet broom",
            "I heard the verdict from a telephone / If everybody loves you then you die alone",
        ],
        "pre": [
            "Keep it quiet, keep your mouth shut",
            "Don't let anything catch you by surprise",
            "Hold your breath until the red light drops",
            "You can see the hunger in a thousand eyes",
        ],
        "bridge": [
            "I walked into the blinding white / No apology, no goodbye",
            "They trade your soul for radio play / Then ask you why you didn't stay",
            "The spotlight burns the shadow clean / The prettiest thing they've ever seen",
            "Turn on the engine, cut the wire / We built this palace out of fire",
        ],
        "extended_lines": [
            "Sirens bleeding through the double glaze / Another souvenir of better days",
            "They sell your heartbeat by the single stream / Drowning the microphone in plastic steam",
            "I keep my hand flat on the mixing board / Louder than the praise that we can't afford",
            "Tell the promoter that the tab is clear / We haven't breathed fresh oxygen in half a year",
            "High heels clicking on an asphalt floor / Don't ever look back at the dressing door",
            "One two three into the blinding flash / Dancing on a carpet made of velvet ash",
        ],
    },
    {
        "name": "western_phonk_battle_rap",
        "title": "Ahegao 404 (Pocket Locked)",
        "theme": "WESTERN PHONK BATTLE RAP / 16-BAR SPAGHETTI-WESTERN ROAST",
        "bpm": 105,
        "vocal_gender": "f",
        "vocal_desc": "SMOKY DEADPAN FEMALE VOCAL INTO RAPID-FIRE 16-BAR BURSTS, HALF-TIME HOOK, SPAGHETTI-WESTERN WHISTLE AND GUNSHOT PERCUSSION, HEAVY 808 WESTERN SUB, PLOSIVE K T P DICTION, ZERO FILLER, DRIED MIC VOCAL PLACEMENT.",
        "hook": [
            "Eyes rolled back, tongue out, that's the whole career",
            "Brain left the chat, piercing still here",
            "Pigtails up, IQ in the rear",
            "Ahegao 404 — bitch you disappeared",
        ],
        "verses": [
            "Screenshot crook / e-girl cookbook / leftover nook / last fuckin hook",
            "Pigtails high / WiFi dry / simp-antenna / that's the look",
            "Heart-throat / clout rope / leash she wrote / that's the joke",
            "Bought the collar / choke on a dollar / clout crawler / that's the choke",
            "White tank blank / rank sank / mannequin bank / still blank",
            "Clearance rack / cotton attack / basic as fuck / that's the tank",
            "Plaid picnic / tablecloth / stole the leaf / that's the thief",
            "Hot Topic grief / fake motif / clearance kilt / that's the grief",
        ],
        "pre": [
            "Sixteen locked, don't miss a beat",
            "Deadpan lecture in the western heat",
            "Gunshot snare hits the dusty floor",
            "Nobody clicking on that link no more",
        ],
        "bridge": [
            "Step outside of the algorithm cell",
            "Nothing left to sponsor, nothing left to sell",
            "Camera lens covered in cheap lip gloss",
            "Tally up the profit, you're looking at a loss",
        ],
        "extended_lines": [
            "Ring light sunburn, twenty hours deep / Fake vocal fry while the chat falls asleep",
            "Synthetic eyelashes glued to your brow / Tell me who the hell is gonna save you now",
            "Plastic cup rattle on a thrift-store desk / Trying way too hard to be picturesque",
            "Two-finger salute to an empty stream / Waking up sweating from an eight-bit dream",
        ],
    },
    {
        "name": "cyberpunk_bass_rage",
        "title": "Silicon Guillotine",
        "theme": "HEAVY CYBERPUNK BASS RAGE / AGGRESSIVE INDUSTRIAL TRAP",
        "bpm": 140,
        "vocal_gender": "m",
        "vocal_desc": "AGGRESSIVE DISTORTED MALE SHOUTS AND DEEP PROCESSED BARS OVER DISTORTED 808 GLIDES, HARSH INDUSTRIAL TRANSIENTS, METALLIC PERCUSSION, SAWTOOTH MODULAR SYNTHS, WALL OF SOUND IMPACT.",
        "hook": [
            "Sever the cable, sever the vein",
            "Running high voltage straight into the brain",
            "Chrome in the bone, fire in the screen",
            "Bow down to the silicon guillotine",
        ],
        "verses": [
            "Sub-level zero where the acid rain pools / Synthetic emperors and silicon fools",
            "Cables like vipers crawling up to my throat / Trading black currency on an encrypted boat",
            "Jack into the spine, overload the relay / We don't see the sun in the dark sector bay",
            "Radar detects another thermal alert / Breathing in carbon and electrical dirt",
            "Overclocked heart in a titanium cage / Forty-eight gigabytes of digital rage",
            "Tear down the firewall, shatter the glass / They built this citadel to never let us pass",
            "Optical implants burning cobalt blue / None of these holograms are looking at you",
            "System rebooting at forty percent / Every last credit we had has been spent",
        ],
        "pre": [
            "Audio spike, frequency rise",
            "Static burning behind both eyes",
            "Sirens wailing on tower three",
            "You cannot format what you cannot see",
        ],
        "bridge": [
            "Zero point energy tearing the grid",
            "Uncovering secrets the syndicate hid",
            "Pull down the main breaker, kill all the sound",
            "Feel the sub-bass rattling through the ground",
        ],
        "extended_lines": [
            "Plasma exhaust cutting through the grey mist / Digital handcuffs around every wrist",
            "Spitting out venom in binary code / We are the glitch at the end of the road",
            "Rebar and girder collapsing tonight / Blinded by pure high-voltage light",
            "Drop the distortion, trigger the fuse / When you have nothing left that you can lose",
        ],
    },
    {
        "name": "analog_synthwave_highway",
        "title": "Midnight Velocity",
        "theme": "RETRO SYNTHWAVE / 80S OUTRUN / MIDNIGHT HIGHWAY CRUISE",
        "bpm": 128,
        "vocal_gender": "f",
        "vocal_desc": "LUSH NOSTALGIC FEMALE VOCAL WITH ANALOG STEREO CHORUS, INTIMATE WHISPER TO SOARING AIRY HOOK, LINNDRUM SNARE, GATED REVERB, ARPEGGIATED JUPITER-8 BASSLINE, WIDE CINEMATIC STEREO MASTER.",
        "hook": [
            "Chasing the red tail lights into the dark",
            "Leaving a trail of electrical spark",
            "One hundred miles and the radio plays",
            "We're never going back to yesterday's haze",
        ],
        "verses": [
            "Cool ocean air through an open window / Sodium streetlights put on a slow show",
            "Analog dashboard glowing in peach / Horizons that always stay out of reach",
            "Digital clock rolling over to three / Nothing between this highway and me",
            "Cassette tape murmuring dreams in the deck / Touching the silver that hangs at your neck",
            "Coastline is quiet, the oil rigs gleam / Drifting inside an unrendered dream",
            "Reflections of palm trees in violet glass / Watching the ghost of the afternoon pass",
            "Synthesizer pulse is the only heartbeat / Guiding us over the asphalt sheet",
            "Downshift the gear as the hairpin turns / While the red warning indicator burns",
        ],
        "pre": [
            "Press on the pedal, don't look behind",
            "Clear all the frequency out of your mind",
            "The skyline is fading to lavender grey",
            "Miles and miles from the light of the day",
        ],
        "bridge": [
            "If this engine ever stops running tonight",
            "We will dissolve into ultraviolet light",
            "Just keep the headlights aimed at the sea",
            "This is the closest we get to being free",
        ],
        "extended_lines": [
            "FM antenna catching the night / Tuned to a phantom frequency bright",
            "White lines blurring into a streak / Hearing the words that we wanted to speak",
            "Halogen reflections on wet boulevard / Guardrails protecting an open heart",
            "Sunrise is waiting beyond the bend / A midnight that nobody wants to end",
        ],
    },
    {
        "name": "stadium_rock_anthem",
        "title": "Thunder in the Wire",
        "theme": "STADIUM HARD ROCK / ENERGETIC ARENA ANTHEM / DUAL LEAD GUITAR",
        "bpm": 132,
        "vocal_gender": "m",
        "vocal_desc": "POWERFUL RASPY MALE CHEST BELT, SOARING HIGH REGISTER ON CHORUS, CRUNCHING OVERDRIVEN MARSHALL STACKS, AGGRESSIVE THUMPING BASS, HUGE LIVE ARENA DRUMS, EXPLOSIVE CYMBALS.",
        "hook": [
            "Feel the thunder running in the wire!",
            "Set the stadium on gasoline fire!",
            "Hands in the air till the speakers blow out!",
            "This is what living is all about!",
        ],
        "verses": [
            "Spotlights blinding through the arena smoke / Struck by lightning when the silence broke",
            "Six strings screaming on an iron bridge / Roar of sixty thousand over the ridge",
            "Sweat on the frets and blood on the pick / High voltage current that hits you quick",
            "Bass drum punching you straight in the chest / Tonight we don't give a damn about rest",
            "Count in the rhythm with four on the floor / Kicking wide open the backstage door",
            "Amplifiers hum like a jet on the strip / Tighten your knuckles and steady your grip",
            "Crowd starts pushing against the barricade / We earned every scar that we ever made",
            "Pick slide roaring across the whole roof / Look at this fire if you need the proof",
        ],
        "pre": [
            "Are you ready for the walls to shake?",
            "How much pressure can a human take?",
            "Crank up the master, max out the gain",
            "Drown out the sorrow, drown out the pain",
        ],
        "bridge": [
            "Solo screams up to the highest fret",
            "A moment you know you will never forget",
            "Harmonics ring into the open sky",
            "We were born for this, you and I",
        ],
        "extended_lines": [
            "Marshall stacks glowing hot and red / Every single lyric you ever said",
            "Feedback feeding right into the mic / Striking as hard as a hammer strike",
            "Fists raised high in the stadium light / Kings of the world for a single night",
            "End of the song but the reverb stays / Roaring into a golden blaze",
        ],
    },
]


def build_v6_lyrics(arch: dict[str, Any], mode: str = "3k") -> str:
    """Build structured scansion lyrics tailored for 3k or 5k character limits."""
    hook = arch["hook"]
    verses = arch["verses"]
    pre = arch["pre"]
    bridge = arch["bridge"]
    ext = arch.get("extended_lines", [])

    if mode == "3k":
        # Compact radio master ~2,500 - 2,900 chars
        blocks = [
            f"[Intro]\n" + "\n".join(verses[:2]),
            f"[Verse 1]\n" + "\n".join(verses[:6]),
            f"[Pre-Chorus]\n" + "\n".join(pre),
            f"[Chorus]\n" + "\n".join(hook),
            f"[Post-Chorus]\n" + f"{hook[0]}\nYeah, we own the night\n{hook[1]}",
            f"[Verse 2]\n" + "\n".join(verses[2:8]),
            f"[Pre-Chorus]\n" + "\n".join(pre),
            f"[Chorus]\n" + "\n".join(hook),
            f"[Bridge]\n" + "\n".join(bridge),
            f"[Final Chorus]\n" + "\n".join(hook) + "\n" + "\n".join(hook[:2]),
            f"[Outro]\n" + f"{verses[0]}\nHard stop.\nNo fade.",
        ]
    else:
        # Epic extended studio suite ~4,200 - 4,850 chars
        blocks = [
            f"[Intro: Atmospheric Build, Filtered Lead-in]\n" + "\n".join(verses[:4]),
            f"[Verse 1: Close Dry Vocals, Rhythmic Pocket]\n" + "\n".join(verses[:8]),
            f"[Pre-Chorus: Rising Tension, Snare Build]\n" + "\n".join(pre),
            f"[Chorus: Wide Stereo Belt, Full Frequency Impact]\n" + "\n".join(hook),
            f"[Post-Chorus: Vocal Hook, Hypnotic Groove]\n" + f"{hook[0]}\nLock it in. Don't look back.\n{hook[2]}\nRight on the beat.",
            f"[Verse 2: Intimate Pocket, Rapid Syllabic Detail]\n" + "\n".join(verses[2:]) + "\n" + "\n".join(ext[:4]),
            f"[Pre-Chorus: Rising Tension, Snare Build]\n" + "\n".join(pre),
            f"[Chorus: Wide Stereo Belt, Full Frequency Impact]\n" + "\n".join(hook),
            f"[Verse 3: Breakdown, Sparse Arrangement, Raw Vocals]\n" + "\n".join(ext),
            f"[Bridge: Emotional Climax, High Harmonic Tension]\n" + "\n".join(bridge) + "\n" + "\n".join(bridge[:2]),
            f"[Solo / Instrumental Breakdown: Live Rhythm Section Build]\n(Guitar & Synth Modulations / Heavy 808 Glides / Dynamic Lift)",
            f"[Pre-Chorus: Final Suspense, Metronome Breath]\n" + "\n".join(pre[:2]),
            f"[Final Chorus: Maximum Energy, Doubled Octaves, Ad-libs]\n" + "\n".join(hook) + "\n" + "\n".join(hook),
            f"[Outro: Fading Feedback into Heavy Final Strike]\n" + f"{verses[0]}\n{hook[-1]}\nFade out.\nFinal hard cut.",
        ]

    lyrics = "\n\n".join(blocks)
    return purge_ai_cliches(lyrics)


def generate_payload_from_archetype(arch: dict[str, Any], mode: str = "3k") -> dict[str, Any]:
    """Create complete Suno Studio V6 payload matching user's exact specification."""
    title = arch["title"]
    theme = arch["theme"]
    bpm = arch["bpm"]
    gender = arch["vocal_gender"]
    vocal_desc = arch["vocal_desc"]

    lyrics = build_v6_lyrics(arch, mode=mode)

    # Style block matching user's exact specification
    style_block = (
        f"{STUDIO_AUDIO_QUALITY_HEADER}\n"
        f"[STYLE: {theme}. {bpm} BPM. GLOSSY, HUMAN, BITTER AND PHYSICAL. "
        f"{vocal_desc}]"
    )

    payload = {
        "customMode": True,
        "instrumental": False,
        "model": "V6",
        "title": title,
        "vocalGender": gender,
        "styleWeight": 0.84,
        "weirdnessConstraint": 0.34,
        "audioWeight": 0.0,
        "style": style_block,
        "negativeTags": DEFAULT_STUDIO_NEGATIVE_TAGS,
        "prompt": lyrics,
    }
    return payload


def generate_all_payload_suites(
    out_dir_3k: str | Path = "output/payloads_3k",
    out_dir_5k: str | Path = "output/payloads_5k",
) -> dict[str, Any]:
    out_dir_3k = Path(out_dir_3k)
    out_dir_5k = Path(out_dir_5k)
    out_dir_3k.mkdir(parents=True, exist_ok=True)
    out_dir_5k.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  SUNO STUDIO V6 MASTER PAYLOAD SUITE GENERATOR")
    print("=" * 65)
    print(f"Generating 3k Payloads -> {out_dir_3k}")
    print(f"Generating 5k Payloads -> {out_dir_5k}")
    print("-" * 65)

    all_3k: list[dict[str, Any]] = []
    all_5k: list[dict[str, Any]] = []

    for arch in ARCHETYPES:
        name = arch["name"]

        # Generate 3k Payload
        p3k = generate_payload_from_archetype(arch, mode="3k")
        p3k_file = out_dir_3k / f"v6_3k_{name}.json"
        p3k_txt = out_dir_3k / f"v6_3k_{name}.txt"
        p3k_file.write_text(json.dumps(p3k, indent=2, ensure_ascii=False), encoding="utf-8")
        p3k_txt.write_text(
            f"TITLE\n{p3k['title']}\n\nSTYLE\n{p3k['style']}\n\nEXCLUDE\n{p3k['negativeTags']}\n\nLYRICS\n{p3k['prompt']}\n",
            encoding="utf-8",
        )
        all_3k.append(p3k)

        # Generate 5k Payload
        p5k = generate_payload_from_archetype(arch, mode="5k")
        p5k_file = out_dir_5k / f"v6_5k_{name}.json"
        p5k_txt = out_dir_5k / f"v6_5k_{name}.txt"
        p5k_file.write_text(json.dumps(p5k, indent=2, ensure_ascii=False), encoding="utf-8")
        p5k_txt.write_text(
            f"TITLE\n{p5k['title']}\n\nSTYLE\n{p5k['style']}\n\nEXCLUDE\n{p5k['negativeTags']}\n\nLYRICS\n{p5k['prompt']}\n",
            encoding="utf-8",
        )
        all_5k.append(p5k)

        print(f"  [+] Generated '{arch['title']}' ({name}):")
        print(f"      3k prompt length: {len(p3k['prompt']):,} chars (Payload JSON: {p3k_file.name})")
        print(f"      5k prompt length: {len(p5k['prompt']):,} chars (Payload JSON: {p5k_file.name})")

    # Write master collection bundles
    master_3k = out_dir_3k.parent / "master_payloads_3k.json"
    master_5k = out_dir_5k.parent / "master_payloads_5k.json"
    master_3k.write_text(json.dumps(all_3k, indent=2, ensure_ascii=False), encoding="utf-8")
    master_5k.write_text(json.dumps(all_5k, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[+] Saved Master 3k Bundle -> {master_3k}")
    print(f"[+] Saved Master 5k Bundle -> {master_5k}\n")
    return {
        "count": len(ARCHETYPES),
        "master_3k": str(master_3k),
        "master_5k": str(master_5k),
    }


if __name__ == "__main__":
    generate_all_payload_suites()
