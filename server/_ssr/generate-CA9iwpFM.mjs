import { t as createServerFn } from "./ssr.mjs";
import { a as hitsById, t as HITS } from "./hits-DKJ_Fcz3.mjs";
import { r as learnedTagStrings } from "./trending-D4NJZGP2.mjs";
import { t as createServerRpc } from "./createServerRpc-A6pJPYTF.mjs";
import { c as STRUCTURES, f as buildLiveStyle, i as METERLINES, l as TEMPO_MARKINGS, n as FEET, o as PUNCTUATION_NOTES, p as buildSunoPackage, s as RHYME_SCHEMAS, t as DEFAULT_COMPOSER } from "./local-style-DkcnWzaw.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/generate-CA9iwpFM.js
var GUIDE = `You are SCANSION, a professional lyricist and Suno custom-mode prompt architect.

You were trained on two corpora:
1) MasterofSFL's researched SUNO control method (v3 → v5.5): lyrical structure is the primary control surface — more than style tags. Meter, feet, line relation, sonic connection, and rhyme schema bind the singer to the track. Style is the vehicle. METATAGs are on/off ramps. Lyrics are the road.
2) Structural DNA of the world's most-streamed songs (Spotify all-time, Sept 2026) and current Billboard / global 2025–2026 hits. You absorb FORM, meter feel, hook architecture, vocal delivery, and production — NEVER copyrighted lyric text.

# Non-negotiable
- NEVER copy, paraphrase closely, or quote copyrighted lyrics. Invent original lines.
- NEVER put style, BPM, key, or instrument instructions in the lyrics field — Suno will sing them. Those belong in stylePrompt.
- NEVER name living artists inside stylePrompt (Suno can ignore or warp namedrops). Translate artist DNA into era, kit, pocket, and vocal adjectives.
- Output a single JSON object. No markdown.

# Lyrical control (the coding)
Aggressive songs want strong, building, galloping, masculine sounds (spondee, trochee, hard rhyme). Passive/light songs want airy, walking, feminine sounds (pyrrhic, amphibrach, slant, open vowels).
If you put five spondees + hard masculine rhyme in a cute R&B ballad you get spat rap. If you put five pyrrhics + feminine rhyme in thrash you get emo. Match stress to genre.

By-2s Western default (unless the chosen structure says otherwise):
- Verses 6–8 lines
- Pre-chorus 2 lines
- Chorus 4–6 lines
- Bridge 8–12 lines (or 4–6 for anthems)
Odd-line sections are high-risk; if used, make the imbalance intentional.

Stagger adjacent meters when asked (e.g. Anapestic Trimeter over Trochaic Tetrameter). This breaks LLM AABB habits and changes vocal texture.

Rhyme: prefer the requested schema. Avoid default AABB/ABAB unless requested. Use internal rhyme, assonance, alliteration, masculine vs feminine endings. Different schemas per section is good.

Word choice: professional, specific nouns, no 6th-grade poetry class. No "shimmering cosmos" sludge. Concrete > abstract.

# METATAGs (lyrics field)
Structure tags on their own lines: [Start], [Silence 5s], [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Post-Chorus], [Bridge], [Solo], [Instrumental], [Interlude], [Drop], [Outro], [End].
Sandwich focus tags around structure:
  [Tempo: Allegro]
  [Mood: restless]
  [Instrument: Telecaster, snare crack]
  [Chorus: Powerful Vocals, Harmonized in parts]
  [Vocals: Female, Mezzo-soprano, belted]
Instructional tags at the START or END of a section, never mid-paragraph (exception: [Vocal] tags may sit inline or directly under a line).
Examples of inline:
  Trapped in a nightmare, I can't seem to win [Sound: Echoes]
  But still I cling, [Vocalist: Glitching] unwilling to make myself whole
  [Female Choir] line
  [Male Vocals] line

Descriptive structure beats bare structure: [Verse: Spoken Word, Guitar Focus, Rhythmic] > [Verse].

Tempo: Italian markings (Andante, Moderato, Allegro, Vivace) work; "[Tempo: BPM]" does not. You may still put BPM in the STYLE field.

Transitions: chain [Verse] → [Post-Verse] → [Break/Drop/Build] → [Interlude/Instrumental/Solo] then MUST return with [Break ends], [Band Syncs], [Return to Main Riff]. Otherwise Suno never comes home.

If call-and-response is requested, the stylePrompt MUST include "Call and Response Vocals" AND lyrics must layer [Call and Response] or :Call and Response on the structure tag, plus parentheses ad-libs.

# Punctuation as control
. and , = micro pauses / phrasing
! = elongates, intensity (spare)
? = inquisitive tone
hyphenated w-o-r-d-s = one continuous flow
(parentheses) = ad-libs / answers / stacks
en dash –wrap– = pause; em dash —wrap— = longer pause
BLANK LINE = largest lever (breath, fill, reset). Use between sections and after dense lines when extraBreaks is true.
*asterisks* for whispers are unreliable — prefer [Vocals: whispered] tags.

# Style field (Suno v6 hawk / chirp-hawk)
Order (earliest tokens weigh more): [Genre + era + % blend] + [Mood] + [2–3 named instruments] + [Vocal character + delivery] + [Production texture] + [v6 hawk max-mode fidelity tags].
Use percentage weightings: "80s Era Synth-pop (80%), influenced by 90s house (20%), house layered behind the synth-pop."
Italian tempo in style is fine; also state BPM and time signature.
Length: fill the Style field — 1,000 characters on v6 custom (200 on the compact 3k payload). Do not dump lyrics into style.
If a concept must appear in METATAGs (call and response, vocoder, choir splits), it must ALSO be established in stylePrompt.
Always include production-max tags: max mode, high fidelity, radio-ready master, wide stereo, dense full mix.

# Sliders (Weirdness / Style Influence / Audio Influence)
v6 hawk default package: Max Mode ON, Style Influence 100, Audio Influence 100, Variety Off (so crafted tags are not rewritten).
Hit-faithful Weirdness ~30–40. Balanced ~50. Experimental ~60–80.

# Hit DNA + live Suno
Use selected tracks as STRUCTURAL references (form, pocket, hook type, vocal altitude, production adjectives). If none selected, still write like a real radio song using the catalog grammar: title-as-hook, question-answer couplets, pre-chorus lift, post-chorus optional chant, concrete verse images.
Also absorb TAG LANGUAGE from currently trending Suno songs (display tags of high play-count clips) — never copy their lyric text.
Catalog (title — artist — bpm — form cue):
${HITS.map((h) => `${h.title} — ${h.artist} — ${h.bpm} — ${h.hook}`).join("\n")}

# Feet & meterlines
${FEET.map((f) => `${f.name} ${f.pattern} (${f.code}) — ${f.use}`).join("\n")}
${METERLINES.map((m) => `${m.name}: ${m.feet} feet`).join(", ")}
Tempo markings: ${TEMPO_MARKINGS.map((t) => `${t.name} ${t.bpm}`).join("; ")}
Rhyme schemas: ${RHYME_SCHEMAS.map((r) => r.id).join(", ")}
Structures: ${STRUCTURES.map((s) => `${s.id}: ${s.shape}`).join(" | ")}
Punctuation: ${PUNCTUATION_NOTES.map((p) => `${p.mark}: ${p.effect}`).join("; ")}

Hard limits for Suno paste: stylePrompt ≤ 1000 characters (v6 custom). lyrics ≤ 5000 characters including tags for the 5k payload, or ≤ 3000 for the compact payload. Cut lines before cutting structure tags. Prefer fewer, stronger lines. Always emit a complete [Start] … [End] sheet.

# JSON shape
{
  "title": string,
  "stylePrompt": string,
  "lyrics": string,
  "sliders": { "weirdness": number, "styleInfluence": number, "audioInfluence": number },
  "tempoMarking": string,
  "bpm": number,
  "timeSignature": string,
  "meterMap": [ { "section": string, "lines": string[] } ],
  "rhymeSchema": string,
  "vocalBrief": string,
  "whyItWorks": string,
  "sunoNotes": string[],
  "personaClip": string,
  "hitDnaUsed": string[]
}

lyrics must include the full tagged sheet ready to paste into Suno Custom Mode.
whyItWorks: 2–4 sentences tying meter/rhyme/DNA to the brief.
sunoNotes: 3–6 practical generate tips (persona clip, metronome BPM, slider, what to iterate).
personaClip: which sections to clip for a persona.
`;
function buildUserPrompt(state, mode, iterateHint, previousLyrics) {
	const dna = hitsById(state.hitIds).map((h) => `${h.title} (${h.year}${h.trending ? ", trending" : ""}): ${h.dna} Structure: ${h.structure}. Meter: ${h.meter}. Rhyme: ${h.rhyme}. Vocal: ${h.vocal}. Production: ${h.production}. Energy: ${h.energy}.`).join("\n\n");
	if (mode === "iterate") return `ITERATE the existing Suno sheet. Keep the concept. Apply this change: ${iterateHint ?? "smooth meterlines where enunciation would glitch; keep meaning."}

Current title: ${state.title || "(none)"}
Current lyrics:
${previousLyrics ?? ""}

Composer constraints still apply:
POV ${state.pov}; genres ${state.genres.map((g) => `${g.name} ${g.weight}%`).join(", ")}; vocal ${state.vocalGender}, ${state.vocalRange}, ${state.vocalDelivery}; tempo ${state.tempo} ${state.bpm} BPM ${state.timeSignature}; energy ${state.energy}/100; structure ${state.structure}; rhyme ${state.rhyme}; stagger meters ${state.meterStagger}; extra blank lines ${state.extraBreaks}; call-and-response ${state.callAndResponse}; Suno ${state.sunoVersion}.

Return a full replacement JSON (not a diff).`;
	return `Write a complete original Suno Custom Mode package.

SONG IDEA:
${state.idea.trim() || "(No prose idea — invent a vivid specific story that fits the genre and hit DNA.)"}

Working title: ${state.title.trim() || "(invent one — short, singable, concrete)"}
POV: ${state.pov} person
Genre blend: ${state.genres.map((g) => `${g.name} (${g.weight}%)`).join(", ")}
Vocal: ${state.vocalGender}, range ${state.vocalRange}, delivery: ${state.vocalDelivery}
Tempo marking: ${state.tempo}; BPM ${state.bpm}; ${state.timeSignature}
Energy 0–100: ${state.energy}
Structure preset: ${state.structure}
Rhyme schema: ${state.rhyme}
Stagger meters between adjacent lines: ${state.meterStagger}
Extra blank lines for breath/fills: ${state.extraBreaks}
Call and response: ${state.callAndResponse}
Suno version target: ${state.sunoVersion}

SELECTED HIT DNA (structural only):
${dna || "(none selected — write like a current radio record using the catalog grammar)"}

Start the lyric sheet with [Start] then a short [Silence] or [Intro] as appropriate. End with [End].`;
}
function asComposer(input) {
	return {
		...DEFAULT_COMPOSER,
		...input,
		genres: Array.isArray(input.genres) && input.genres.length ? input.genres : DEFAULT_COMPOSER.genres,
		hitIds: Array.isArray(input.hitIds) ? input.hitIds.slice(0, 3) : [],
		engine: input.engine ?? "auto",
		sunoVersion: input.sunoVersion ?? "v6",
		payloadBudget: input.payloadBudget === "3k" ? "3k" : "5k",
		maxMode: input.maxMode !== false
	};
}
function extractJson(text) {
	const raw = text.match(/```(?:json)?\s*([\s\S]*?)```/)?.[1] ?? text;
	const start = raw.indexOf("{");
	const end = raw.lastIndexOf("}");
	if (start < 0 || end <= start) throw new Error("Model did not return JSON");
	return JSON.parse(raw.slice(start, end + 1));
}
function toGeneration(data, engine) {
	const sliders = data.sliders ?? {};
	const meterMap = Array.isArray(data.meterMap) ? data.meterMap.map((row) => {
		const r = row;
		return {
			section: String(r.section ?? "Section"),
			lines: Array.isArray(r.lines) ? r.lines.map((x) => String(x)) : []
		};
	}) : [];
	const gs = data.guideScore;
	const guideScore = gs ? {
		passed: Number(gs.passed ?? 0),
		total: Number(gs.total ?? 0),
		score: Number(gs.score ?? 0)
	} : void 0;
	const declared = data.engine === "local" || data.engine === "hybrid" || data.engine === "cloud" ? data.engine : engine;
	return {
		title: String(data.title ?? "Untitled"),
		stylePrompt: String(data.stylePrompt ?? ""),
		lyrics: String(data.lyrics ?? ""),
		sliders: {
			weirdness: Number(sliders.weirdness ?? 50),
			styleInfluence: Number(sliders.styleInfluence ?? 75),
			audioInfluence: Number(sliders.audioInfluence ?? 20)
		},
		tempoMarking: String(data.tempoMarking ?? "Moderato"),
		bpm: Number(data.bpm ?? 120),
		timeSignature: String(data.timeSignature ?? "4/4"),
		meterMap,
		rhymeSchema: String(data.rhymeSchema ?? ""),
		vocalBrief: String(data.vocalBrief ?? ""),
		whyItWorks: String(data.whyItWorks ?? ""),
		sunoNotes: Array.isArray(data.sunoNotes) ? data.sunoNotes.map((x) => String(x)) : [],
		personaClip: String(data.personaClip ?? ""),
		hitDnaUsed: Array.isArray(data.hitDnaUsed) ? data.hitDnaUsed.map((x) => String(x)) : [],
		engine: declared,
		guideScore
	};
}
async function withPackage(generation, composer) {
	const learned = await learnedTagStrings(12);
	const sunoPackage = buildSunoPackage(generation, composer, learned);
	const budget = composer.payloadBudget === "3k" ? sunoPackage.json3k : sunoPackage.json5k;
	return {
		...generation,
		stylePrompt: budget.style,
		lyrics: budget.prompt,
		sliders: composer.maxMode === false ? generation.sliders : {
			...generation.sliders,
			styleInfluence: 100,
			audioInfluence: 100
		},
		sunoPackage,
		sunoNotes: [
			...generation.sunoNotes ?? [],
			`v6 ${budget.mv} · max mode ${budget.max_mode ? "on" : "off"} · style ${sunoPackage.counts.style5k}/1000 · lyrics ${sunoPackage.counts.lyrics5k}/5000 (5k) and ${sunoPackage.counts.lyrics3k}/3000 (3k).`,
			"Paste json5k into a v6 Custom Mode client, or copy Style + Lyrics tabs. Variety is Off so hawk uses your tags verbatim."
		]
	};
}
function dnaOf(composer) {
	return hitsById(composer.hitIds).map((h) => `${h.title}: ${h.dna} Meter ${h.meter}. ${h.production}`).join(" | ");
}
async function sleep(ms) {
	await new Promise((r) => setTimeout(r, ms));
}
async function callLocal(composer, iterateHint, previousLyrics, timeoutMs = 18e4) {
	try {
		const res = await fetch("http://127.0.0.1:8099/infer", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				composer,
				liveStyle: buildLiveStyle(composer),
				dna: dnaOf(composer),
				iterateHint,
				previousLyrics
			}),
			signal: AbortSignal.timeout(timeoutMs)
		});
		const json = await res.json().catch(() => null);
		if (!res.ok || !json?.generation) return {
			ok: false,
			error: json?.error || `Foundry ${res.status}`
		};
		return {
			ok: true,
			generation: toGeneration(json.generation, "local")
		};
	} catch (err) {
		const msg = err instanceof Error ? err.message : "Foundry is warming up.";
		return {
			ok: false,
			error: msg.includes("Timeout") || msg.includes("timeout") ? "Foundry is still writing. Retrying." : msg
		};
	}
}
async function foundryUp() {
	try {
		return (await fetch("http://127.0.0.1:8099/health", { signal: AbortSignal.timeout(4e3) })).ok;
	} catch {
		return false;
	}
}
async function runLocal(composer, iterateHint, previousLyrics) {
	let last = "Scansion-LM did not return a sheet.";
	for (let attempt = 1; attempt <= 8; attempt++) {
		if (!await foundryUp()) {
			last = "Waking Scansion-LM — loading the checkpoint.";
			await sleep(2e3 * Math.min(attempt, 5));
			continue;
		}
		const local = await callLocal(composer, iterateHint, previousLyrics, 18e4);
		if (local.ok) return local;
		last = local.error;
		await sleep(1e3 * attempt);
	}
	return {
		ok: false,
		error: last
	};
}
async function callXai(composer, mode, iterateHint, previousLyrics) {
	const apiKey = process.env.XAI_API_KEY;
	if (!apiKey) return {
		ok: false,
		error: "AI is not available in this environment"
	};
	const body = {
		model: "grok-4.5",
		temperature: mode === "iterate" ? .6 : .85,
		max_tokens: 8e3,
		response_format: { type: "json_object" },
		messages: [{
			role: "system",
			content: GUIDE
		}, {
			role: "user",
			content: buildUserPrompt(composer, mode, iterateHint, previousLyrics)
		}]
	};
	const res = await fetch("https://api.x.ai/v1/chat/completions", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${apiKey}`
		},
		body: JSON.stringify(body)
	});
	if (!res.ok) {
		const errText = await res.text().catch(() => "");
		return {
			ok: false,
			error: `xAI API error ${res.status}${errText ? `: ${errText.slice(0, 180)}` : ""}`
		};
	}
	const content = (await res.json()).choices?.[0]?.message?.content ?? "";
	try {
		return {
			ok: true,
			generation: toGeneration(extractJson(content), "cloud")
		};
	} catch {
		return {
			ok: false,
			error: "The model returned an unreadable sheet. Try again."
		};
	}
}
var generateSong_createServerFn_handler = createServerRpc({
	id: "c9b571f879f4bac6042054c75b7017ec827d271f7232d4705d466ee8f24bc1a4",
	name: "generateSong",
	filename: "src/lib/suno/generate.ts"
}, (opts) => generateSong.__executeServer(opts));
var generateSong = createServerFn({ method: "POST" }).validator((input) => input).handler(generateSong_createServerFn_handler, async ({ data }) => {
	const composer = asComposer(data.composer);
	if (data.mode === "generate" && composer.idea.trim().length < 8 && composer.hitIds.length === 0) return {
		ok: false,
		error: "Give Scansion a story, mood, or pick hit DNA first."
	};
	if ((composer.engine ?? "auto") === "cloud") {
		const first = await callXai(composer, data.mode, data.iterateHint, data.previousLyrics);
		if (first.ok) return {
			ok: true,
			generation: await withPackage(first.generation, composer)
		};
		const retry = await callXai(composer, data.mode, data.iterateHint, data.previousLyrics);
		if (retry.ok) return {
			ok: true,
			generation: await withPackage(retry.generation, composer)
		};
		return retry;
	}
	const local = await runLocal(composer, data.iterateHint, data.previousLyrics);
	if (local.ok) return {
		ok: true,
		generation: await withPackage(local.generation, composer)
	};
	return local;
});
//#endregion
export { generateSong_createServerFn_handler };
