import { a as hitsById } from "./hits-DKJ_Fcz3.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/local-style-DkcnWzaw.js
var BUDGETS = {
	"5k": {
		lyrics: 5e3,
		style: 1e3,
		title: 80,
		negative: 1e3,
		description: 3e3
	},
	"3k": {
		lyrics: 3e3,
		style: 200,
		title: 80,
		negative: 200,
		description: 400
	}
};
var HAWK_MAX_TAGS = "v6 hawk, max mode, high fidelity, radio-ready master, wide stereo, dense full mix, punchy drums, glossy vocal, studio polish, no mud";
var NEGATIVES = "muddy low end, off-key, generic AI wash, spoken wikipedia, karaoke, copyrighted interpolation, thin mix, robotic cadence";
function clipText(s, max) {
	const text = s.replace(/\s+$/g, "");
	if (text.length <= max) return text;
	const cut = text.slice(0, max);
	const nl = cut.lastIndexOf("\n");
	if (nl > max * .55) return cut.slice(0, nl).replace(/\s+$/g, "");
	const sp = Math.max(cut.lastIndexOf(" "), cut.lastIndexOf(","));
	return (sp > max * .55 ? cut.slice(0, sp) : cut).replace(/\s+$/g, "");
}
function modelFor(version) {
	if (version === "v6-wild") return {
		model: "V6_WILD",
		mv: "chirp-hawk-wild"
	};
	if (version === "v6-mini") return {
		model: "V6_MINI",
		mv: "chirp-goose"
	};
	return {
		model: "V6",
		mv: "chirp-hawk"
	};
}
function vocalGender(g) {
	if (g === "male") return "m";
	if (g === "female") return "f";
}
function unit(n) {
	return Math.max(0, Math.min(1, Math.round(n) / 100));
}
function mergeStyle(base, extra, max) {
	const seen = /* @__PURE__ */ new Set();
	const parts = [];
	for (const raw of [base, ...extra]) for (const bit of raw.split(/[,;]+/)) {
		const t = bit.trim().replace(/\s+/g, " ");
		if (!t) continue;
		const key = t.toLowerCase();
		if (seen.has(key)) continue;
		seen.add(key);
		parts.push(t);
	}
	let out = parts.join(", ");
	if (out.length <= max) return out;
	out = "";
	for (const p of parts) {
		const next = out ? `${out}, ${p}` : p;
		if (next.length > max) break;
		out = next;
	}
	return out || clipText(base, max);
}
function buildSunoJson(generation, composer, budget, learnedTags = []) {
	const lim = BUDGETS[budget];
	const { model, mv } = modelFor(composer.sunoVersion);
	const style = mergeStyle(generation.stylePrompt, [HAWK_MAX_TAGS, ...learnedTags], lim.style);
	const prompt = clipText(generation.lyrics, lim.lyrics);
	const title = clipText(generation.title || "Untitled", lim.title);
	const negativeTags = clipText(NEGATIVES, lim.negative);
	const vg = vocalGender(composer.vocalGender);
	const payload = {
		customMode: true,
		instrumental: false,
		model,
		mv,
		title,
		prompt,
		style,
		tags: style,
		negativeTags,
		styleWeight: composer.maxMode === false ? unit(generation.sliders.styleInfluence) : 1,
		weirdnessConstraint: unit(generation.sliders.weirdness),
		audioWeight: composer.maxMode === false ? unit(generation.sliders.audioInfluence) : 1,
		max_mode: composer.maxMode !== false,
		is_max_mode: composer.maxMode !== false,
		variety: "off",
		duration: 360
	};
	if (vg) payload.vocalGender = vg;
	return payload;
}
function hashHue(s) {
	let h = 0;
	for (let i = 0; i < s.length; i++) h = h * 33 + s.charCodeAt(i) >>> 0;
	return h % 360;
}
function buildCoverSvg(title, tags, bpm) {
	const hue = hashHue(title + tags);
	const a = `hsl(${hue} 62% 42%)`;
	const b = `hsl(${(hue + 38) % 360} 48% 28%)`;
	const c = `hsl(${(hue + 190) % 360} 40% 36%)`;
	const safe = title.replace(/[<>&]/g, "").slice(0, 28) || "Scansion";
	const tag = (tags.split(",")[0] || "v6 hawk").trim().slice(0, 22);
	return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1200">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${a}"/>
      <stop offset="1" stop-color="${b}"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="1200" fill="#f4ead8"/>
  <rect x="48" y="48" width="1104" height="1104" rx="36" fill="url(#g)"/>
  <circle cx="600" cy="560" r="268" fill="${c}" opacity="0.55"/>
  <circle cx="600" cy="560" r="92" fill="#fffaf3"/>
  <circle cx="600" cy="560" r="28" fill="#c2412d"/>
  ${[
		0,
		1,
		2,
		3,
		4
	].map((i) => `<rect x="120" y="${140 + i * 18}" width="${420 - i * 24}" height="8" rx="4" fill="#fffaf3" opacity="${.35 - i * .05}"/>`).join("")}
  <text x="96" y="980" fill="#fffaf3" font-family="Georgia, serif" font-size="64" font-style="italic">${escapeXml(safe)}</text>
  <text x="96" y="1048" fill="#f3d2a8" font-family="Figtree, sans-serif" font-size="28" font-weight="600">${escapeXml(tag)} · ${bpm} BPM · chirp-hawk</text>
</svg>`;
}
function escapeXml(s) {
	const map = {
		"&": "&amp;",
		"<": "&lt;",
		">": "&gt;",
		"\"": "&quot;"
	};
	return s.replace(/[&<>"]/g, (ch) => map[ch] ?? ch);
}
function buildCoverPrompt(title, tags) {
	return `Square album cover, 1:1, no text, no logos. ${tags.split(",")[0]?.trim() || "alt-pop"} record sleeve. Warm parchment paper, terracotta and teal ink, vinyl disc motif, staff-ruled texture, cinematic lighting, print-ready, high detail. Mood of "${title}".`;
}
function buildDescription(generation, idea) {
	const core = idea.trim() || generation.stylePrompt;
	return clipText(`${generation.title}. ${generation.tempoMarking} ${generation.bpm} BPM. ${generation.vocalBrief}. ${core} Radio-ready v6 hawk custom mode, max mode, full mix.`, 3e3);
}
function tagListFromStyle(style) {
	return style.split(/[,;]+/).map((t) => t.trim()).filter((t) => t.length > 1).slice(0, 24);
}
function buildSunoPackage(generation, composer, learnedTags = []) {
	const json5k = buildSunoJson(generation, composer, "5k", learnedTags);
	const json3k = buildSunoJson(generation, composer, "3k", learnedTags);
	const tagList = tagListFromStyle(json5k.tags);
	return {
		json5k,
		json3k,
		description: clipText(buildDescription(generation, composer.idea), BUDGETS[composer.payloadBudget ?? "5k"].description),
		coverSvg: buildCoverSvg(generation.title, json5k.tags, generation.bpm),
		coverPrompt: buildCoverPrompt(generation.title, json5k.tags),
		tagList,
		negatives: json5k.negativeTags,
		counts: {
			style5k: json5k.style.length,
			lyrics5k: json5k.prompt.length,
			style3k: json3k.style.length,
			lyrics3k: json3k.prompt.length
		}
	};
}
function crc32(bytes) {
	let c = -1;
	for (let i = 0; i < bytes.length; i++) {
		c ^= bytes[i];
		for (let k = 0; k < 8; k++) c = c >>> 1 ^ 3988292384 & -(c & 1);
	}
	return ~c >>> 0;
}
function u16(n) {
	const b = /* @__PURE__ */ new Uint8Array(2);
	b[0] = n & 255;
	b[1] = n >>> 8 & 255;
	return b;
}
function u32(n) {
	const b = /* @__PURE__ */ new Uint8Array(4);
	b[0] = n & 255;
	b[1] = n >>> 8 & 255;
	b[2] = n >>> 16 & 255;
	b[3] = n >>> 24 & 255;
	return b;
}
function zipStore(files) {
	const locals = [];
	const centrals = [];
	let offset = 0;
	for (const file of files) {
		const name = new TextEncoder().encode(file.name);
		const crc = crc32(file.data);
		const local = concat([
			u32(67324752),
			u16(20),
			u16(0),
			u16(0),
			u16(0),
			u16(0),
			u32(crc),
			u32(file.data.length),
			u32(file.data.length),
			u16(name.length),
			u16(0),
			name,
			file.data
		]);
		const central = concat([
			u32(33639248),
			u16(20),
			u16(20),
			u16(0),
			u16(0),
			u16(0),
			u16(0),
			u32(crc),
			u32(file.data.length),
			u32(file.data.length),
			u16(name.length),
			u16(0),
			u16(0),
			u16(0),
			u16(0),
			u32(0),
			u32(offset),
			name
		]);
		locals.push(local);
		centrals.push(central);
		offset += local.length;
	}
	const centralBlob = concat(centrals);
	const eocd = concat([
		u32(101010256),
		u16(0),
		u16(0),
		u16(files.length),
		u16(files.length),
		u32(centralBlob.length),
		u32(offset),
		u16(0)
	]);
	return new Blob([concat([
		...locals,
		centralBlob,
		eocd
	])], { type: "application/zip" });
}
function concat(parts) {
	const n = parts.reduce((a, p) => a + p.length, 0);
	const out = new Uint8Array(n);
	let o = 0;
	for (const p of parts) {
		out.set(p, o);
		o += p.length;
	}
	return out;
}
function packageZip(pkg, title) {
	const slug = (title || "scansion").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "scansion";
	const enc = new TextEncoder();
	return zipStore([
		{
			name: `${slug}-suno-v6-hawk-5k.json`,
			data: enc.encode(JSON.stringify(pkg.json5k, null, 2))
		},
		{
			name: `${slug}-suno-v6-hawk-3k.json`,
			data: enc.encode(JSON.stringify(pkg.json3k, null, 2))
		},
		{
			name: `${slug}-lyrics.txt`,
			data: enc.encode(pkg.json5k.prompt)
		},
		{
			name: `${slug}-style.txt`,
			data: enc.encode(pkg.json5k.style)
		},
		{
			name: `${slug}-description.txt`,
			data: enc.encode(pkg.description)
		},
		{
			name: `${slug}-cover-prompt.txt`,
			data: enc.encode(pkg.coverPrompt)
		},
		{
			name: `${slug}-cover.svg`,
			data: enc.encode(pkg.coverSvg)
		},
		{
			name: `${slug}-tags.json`,
			data: enc.encode(JSON.stringify({
				tags: pkg.tagList,
				negatives: pkg.negatives
			}, null, 2))
		}
	]);
}
function downloadBlob(blob, filename) {
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.rel = "noopener";
	document.body.appendChild(a);
	a.click();
	a.remove();
	window.setTimeout(() => URL.revokeObjectURL(url), 1500);
}
var TEMPO_MARKINGS = [
	{
		name: "Largo",
		bpm: "40–60",
		feel: "Very slow, weighty"
	},
	{
		name: "Adagio",
		bpm: "66–76",
		feel: "Slow, expressive"
	},
	{
		name: "Andante",
		bpm: "76–108",
		feel: "Walking pace"
	},
	{
		name: "Moderato",
		bpm: "108–120",
		feel: "Moderate"
	},
	{
		name: "Allegretto",
		bpm: "112–120",
		feel: "Fairly brisk"
	},
	{
		name: "Allegro",
		bpm: "120–156",
		feel: "Fast, bright"
	},
	{
		name: "Vivace",
		bpm: "156–176",
		feel: "Lively, vivid"
	},
	{
		name: "Presto",
		bpm: "168–200",
		feel: "Very fast"
	}
];
var FEET = [
	{
		name: "Iamb",
		pattern: "da-DUM",
		code: "u /",
		use: "Speech, pop, hymns"
	},
	{
		name: "Trochee",
		pattern: "DUM-da",
		code: "/ u",
		use: "Chants, marches, spells"
	},
	{
		name: "Spondee",
		pattern: "DUM-DUM",
		code: "/ /",
		use: "Impact, aggression, stops"
	},
	{
		name: "Pyrrhic",
		pattern: "da-da",
		code: "u u",
		use: "Air, glide, feminine flow"
	},
	{
		name: "Anapest",
		pattern: "da-da-DUM",
		code: "u u /",
		use: "Gallop, drive, storytelling"
	},
	{
		name: "Dactyl",
		pattern: "DUM-da-da",
		code: "/ u u",
		use: "Waltz, descent, epic"
	},
	{
		name: "Amphibrach",
		pattern: "da-DUM-da",
		code: "u / u",
		use: "Bounce, country, swing"
	}
];
var METERLINES = [
	{
		name: "Monometer",
		feet: 1
	},
	{
		name: "Dimeter",
		feet: 2
	},
	{
		name: "Trimeter",
		feet: 3
	},
	{
		name: "Tetrameter",
		feet: 4
	},
	{
		name: "Pentameter",
		feet: 5
	},
	{
		name: "Hexameter",
		feet: 6
	}
];
var RHYME_SCHEMAS = [
	{
		id: "AABB",
		label: "Couplets AABB",
		note: "Default — avoid unless you want generic"
	},
	{
		id: "ABAB",
		label: "Alternate ABAB",
		note: "Classic pop verse"
	},
	{
		id: "ABCB",
		label: "Ballad ABCB",
		note: "Story verses, country, folk"
	},
	{
		id: "AABC",
		label: "AABC",
		note: "Setup then open"
	},
	{
		id: "ABCA",
		label: "Envelope ABCA",
		note: "Returns to the start sound"
	},
	{
		id: "ABCCBA",
		label: "Mirror ABCCBA",
		note: "Chorus architecture"
	},
	{
		id: "ABCABC",
		label: "Repeat ABCABC",
		note: "Hook cycles"
	},
	{
		id: "ABCDBA",
		label: "ABCDBA",
		note: "Narrative turn"
	},
	{
		id: "XAXA",
		label: "Refrain XAXA",
		note: "Title-line as B rhyme"
	}
];
var GENRE_OPTIONS = [
	"Pop",
	"Synth-pop",
	"Indie pop",
	"Alt-pop",
	"Dance-pop",
	"R&B",
	"Contemporary R&B",
	"Soul",
	"Hip-hop",
	"Trap",
	"Boom bap",
	"Country",
	"Country pop",
	"Americana",
	"Folk",
	"Indie folk",
	"Rock",
	"Indie rock",
	"Arena rock",
	"Punk",
	"Pop-punk",
	"Alternative",
	"Grunge",
	"Metal",
	"Thrash metal",
	"Nu-metal",
	"Metalcore",
	"EDM",
	"House",
	"Techno",
	"Hyperpop",
	"Afrobeats",
	"Reggaeton",
	"Latin pop",
	"K-pop",
	"Disco",
	"Funk",
	"Gospel",
	"Ballad",
	"Singer-songwriter",
	"Dream pop",
	"Shoegaze",
	"Phonk",
	"Drill"
];
var STRUCTURES = [
	{
		id: "standard",
		label: "Standard hit",
		shape: "Intro → V1 → Pre → Chorus → V2 → Pre → Chorus → Bridge → Chorus → Outro",
		lines: {
			verse: "6–8",
			pre: "2",
			chorus: "4–6",
			bridge: "8–12"
		}
	},
	{
		id: "anthem",
		label: "Anthem",
		shape: "Cold intro hook → V1 → Chorus → V2 → Chorus → Post → Bridge → Double chorus",
		lines: {
			verse: "4–6",
			pre: "2",
			chorus: "8",
			bridge: "4–6"
		}
	},
	{
		id: "ballad",
		label: "Ballad",
		shape: "Intro → V1 → V2 → Chorus → V3 → Chorus → Bridge → Final chorus",
		lines: {
			verse: "8",
			pre: "0–2",
			chorus: "6",
			bridge: "6–8"
		}
	},
	{
		id: "rap",
		label: "Rap / story",
		shape: "Intro tag → 16 V1 → Hook → 16 V2 → Hook → Bridge/break → Hook",
		lines: {
			verse: "8–16",
			pre: "0–2",
			chorus: "4–8",
			bridge: "4–8"
		}
	},
	{
		id: "edm",
		label: "EDM",
		shape: "Intro → Build → Drop (hook) → Breakdown verse → Build → Drop → Outro",
		lines: {
			verse: "4–8",
			pre: "2–4",
			chorus: "4–8",
			bridge: "4"
		}
	},
	{
		id: "country",
		label: "Country story",
		shape: "Intro lick → V1 → Chorus → V2 → Chorus → Bridge → Chorus tag",
		lines: {
			verse: "6–8",
			pre: "0–2",
			chorus: "6",
			bridge: "4–6"
		}
	}
];
var VOCAL_RANGES = [
	"Unspecified",
	"Bass",
	"Baritone",
	"Tenor",
	"Alto",
	"Mezzo-soprano",
	"Soprano",
	"Falsetto lead",
	"Spoken-sung"
];
var VOCAL_DELIVERIES = [
	"Intimate, close-mic, breathy",
	"Conversational, dry, present",
	"Raspy, gritty, chest-forward",
	"Belted, anthemic, open throat",
	"Whisper to belt dynamics",
	"Melismatic R&B runs",
	"Rap-sung hybrid",
	"Choir stacked harmonies",
	"Call and response",
	"Glitched, chopped, processed"
];
var PUNCTUATION_NOTES = [
	{
		mark: "Period .",
		effect: "Subtle pause; beat emphasis"
	},
	{
		mark: "Comma ,",
		effect: "Phrasing; clarifies breath"
	},
	{
		mark: "Exclaim !",
		effect: "Elongates; intensity (use sparingly on v4+)"
	},
	{
		mark: "Question ?",
		effect: "Curious / interrogative tone"
	},
	{
		mark: "Hyphen a-b-c",
		effect: "Sung as one continuous flow"
	},
	{
		mark: "Parentheses ()",
		effect: "Ad-libs, call-response, background"
	},
	{
		mark: "En dash –text–",
		effect: "Pause / break around the wrap"
	},
	{
		mark: "Em dash —text—",
		effect: "Longer pause / break"
	},
	{
		mark: "Blank line",
		effect: "Biggest lever — breath, fill, reset"
	}
];
var DEFAULT_COMPOSER = {
	idea: "",
	title: "",
	pov: "first",
	genres: [{
		name: "Alt-pop",
		weight: 70
	}, {
		name: "Indie rock",
		weight: 30
	}],
	vocalGender: "unspecified",
	vocalRange: "Unspecified",
	vocalDelivery: "Conversational, dry, present",
	tempo: "Moderato",
	bpm: 112,
	timeSignature: "4/4",
	energy: 55,
	structure: "standard",
	rhyme: "ABCB",
	meterStagger: true,
	extraBreaks: true,
	callAndResponse: false,
	hitIds: [],
	sunoVersion: "v6",
	engine: "auto",
	payloadBudget: "5k",
	maxMode: true
};
var PRESETS = [
	{
		id: "mojave",
		label: "Mojave bars",
		blurb: "Gritty survival anthem from the guide's case study.",
		patch: {
			idea: "A man scraping survival out of the Mojave. Third-person, heat, dust, desperation turning into stubborn will.",
			title: "Mojave Bars",
			pov: "third",
			genres: [{
				name: "Rock",
				weight: 70
			}, {
				name: "Thrash metal",
				weight: 30
			}],
			vocalGender: "male",
			vocalRange: "Baritone",
			vocalDelivery: "Raspy, gritty, chest-forward",
			tempo: "Allegro",
			bpm: 115,
			energy: 78,
			structure: "standard",
			rhyme: "ABAB",
			meterStagger: true,
			extraBreaks: true,
			callAndResponse: false
		}
	},
	{
		id: "night-drive",
		label: "Night drive",
		blurb: "Synth-pop four-on-the-floor, neon afterglow, falsetto hook.",
		patch: {
			idea: "Driving the empty freeway after a fight you cannot unsay. The city is still lit. You keep the windows down so the night can argue back.",
			title: "",
			pov: "first",
			genres: [{
				name: "Synth-pop",
				weight: 80
			}, {
				name: "Dance-pop",
				weight: 20
			}],
			vocalGender: "male",
			vocalRange: "Falsetto lead",
			vocalDelivery: "Whisper to belt dynamics",
			tempo: "Allegro",
			bpm: 171,
			energy: 72,
			structure: "anthem",
			rhyme: "ABAB",
			meterStagger: true,
			extraBreaks: true,
			callAndResponse: false
		}
	},
	{
		id: "texas",
		label: "Choosin' country",
		blurb: "Story-first country-pop, chantable title hook, 2026 radio.",
		patch: {
			idea: "Leaving a city love for the place that still knows your real name. Pride and ache in the same sentence. Truck-cab confession that becomes a bar chorus.",
			title: "",
			pov: "first",
			genres: [{
				name: "Country",
				weight: 75
			}, {
				name: "Country pop",
				weight: 25
			}],
			vocalGender: "female",
			vocalRange: "Mezzo-soprano",
			vocalDelivery: "Belted, anthemic, open throat",
			tempo: "Moderato",
			bpm: 148,
			energy: 68,
			structure: "country",
			rhyme: "ABCB",
			meterStagger: true,
			extraBreaks: true,
			callAndResponse: true
		}
	},
	{
		id: "confession",
		label: "Quiet confession",
		blurb: "Close-mic indie, whispered verses, exploding chorus.",
		patch: {
			idea: "Admitting you still wait for someone who already moved on. Soft until it isn't. The chorus is the thing you never said in the room.",
			title: "",
			pov: "second",
			genres: [{
				name: "Alt-pop",
				weight: 60
			}, {
				name: "Indie folk",
				weight: 40
			}],
			vocalGender: "female",
			vocalRange: "Alto",
			vocalDelivery: "Intimate, close-mic, breathy",
			tempo: "Andante",
			bpm: 96,
			energy: 42,
			structure: "ballad",
			rhyme: "XAXA",
			meterStagger: true,
			extraBreaks: true,
			callAndResponse: false
		}
	},
	{
		id: "club",
		label: "Club steel",
		blurb: "Four-bar chant hook, stacked vocals, drop architecture.",
		patch: {
			idea: "A night that refuses to end. Bodies, lights, a name you keep saying like a spell. The drop is the title.",
			title: "",
			pov: "first",
			genres: [{
				name: "House",
				weight: 55
			}, {
				name: "Dance-pop",
				weight: 45
			}],
			vocalGender: "unspecified",
			vocalRange: "Unspecified",
			vocalDelivery: "Choir stacked harmonies",
			tempo: "Allegro",
			bpm: 124,
			energy: 82,
			structure: "edm",
			rhyme: "ABCABC",
			meterStagger: false,
			extraBreaks: true,
			callAndResponse: true
		}
	}
];
function energyWord(n) {
	if (n < 35) return "restrained, airy, walking feel";
	if (n < 55) return "moderate drive, room to breathe";
	if (n < 75) return "forward motion, chest-forward";
	return "high tension, galloping, masculine stress";
}
function buildLiveStyle(state) {
	const genres = [...state.genres].filter((g) => g.weight > 0 && g.name.trim()).sort((a, b) => b.weight - a.weight);
	const genreStr = genres.length > 0 ? genres.map((g) => `${g.name} (${g.weight}%)`).join(", ") : "Alt-pop (100%)";
	const hits = hitsById(state.hitIds);
	const fromHits = hits.map((h) => h.production.split(",")[0]?.trim()).filter(Boolean).slice(0, 3);
	const vocalBits = [
		state.vocalGender !== "unspecified" ? `${state.vocalGender} lead` : null,
		state.vocalRange !== "Unspecified" ? state.vocalRange : null,
		state.vocalDelivery
	].filter(Boolean);
	if (state.callAndResponse) vocalBits.push("call and response vocals");
	const tempo = TEMPO_MARKINGS.find((t) => t.name === state.tempo)?.name ?? state.tempo;
	const structure = STRUCTURES.find((s) => s.id === state.structure);
	return [
		`${genreStr}.`,
		`${tempo} feel, ${state.bpm} BPM, ${state.timeSignature}.`,
		energyWord(state.energy) + ".",
		vocalBits.join(", ") + ".",
		fromHits.length ? `Instrumentation: ${fromHits.join(", ")}.` : null,
		structure ? `Form leans ${structure.label.toLowerCase()}.` : null,
		hits.length ? `Production cues: ${hits.map((h) => h.production).join("; ")}.` : null,
		"v6 hawk, max mode, high fidelity, radio-ready master, wide stereo, dense full mix.",
		"Studio production, distinct sections, no generic AI wash."
	].filter(Boolean).join(" ");
}
function sliderGuess(state) {
	const hitFaithful = state.hitIds.length > 0;
	const experimental = state.energy > 80 || state.meterStagger;
	return {
		weirdness: hitFaithful ? 35 : experimental ? 62 : 48,
		styleInfluence: hitFaithful ? 100 : 100,
		audioInfluence: 100
	};
}
//#endregion
export { PRESETS as a, STRUCTURES as c, VOCAL_RANGES as d, buildLiveStyle as f, sliderGuess as g, packageZip as h, METERLINES as i, TEMPO_MARKINGS as l, downloadBlob as m, FEET as n, PUNCTUATION_NOTES as o, buildSunoPackage as p, GENRE_OPTIONS as r, RHYME_SCHEMAS as s, DEFAULT_COMPOSER as t, VOCAL_DELIVERIES as u };
