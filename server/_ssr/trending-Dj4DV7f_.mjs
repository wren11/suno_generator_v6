import { t as createServerFn } from "./ssr.mjs";
import { t as HITS } from "./hits-DKJ_Fcz3.mjs";
import { t as createServerRpc } from "./createServerRpc-A6pJPYTF.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/trending-Dj4DV7f_.js
var HOME = "https://studio-api-prod.suno.com/api/unified/homepage";
var PLAYLIST = (id, page) => `https://studio-api-prod.suno.com/api/playlist/${id}/?page=${page}`;
var FOUNDRY = "http://127.0.0.1:8099";
var HEADERS = {
	"User-Agent": "Scansion/1.0 (Suno lyric architect; public catalog pull)",
	Accept: "application/json",
	"Content-Type": "application/json",
	Origin: "https://suno.com",
	Referer: "https://suno.com/"
};
var hitTitles = new Set(HITS.map((h) => h.title.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim()));
function looksLikeCover(title) {
	const n = title.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
	if (hitTitles.has(n)) return true;
	for (const t of hitTitles) if (t.length > 6 && (n === t || n.startsWith(`${t} `) || n.endsWith(` ${t}`))) return true;
	return false;
}
async function getJson(url) {
	const res = await fetch(url, {
		headers: HEADERS,
		signal: AbortSignal.timeout(18e3)
	});
	if (!res.ok) throw new Error(`${url} ${res.status}`);
	return await res.json();
}
async function postJson(url, body) {
	const res = await fetch(url, {
		method: "POST",
		headers: HEADERS,
		body: JSON.stringify(body),
		signal: AbortSignal.timeout(18e3)
	});
	if (!res.ok) throw new Error(`${url} ${res.status}`);
	return await res.json();
}
function asRecord(v) {
	return v && typeof v === "object" && !Array.isArray(v) ? v : null;
}
function walkClips(node, acc, playlists) {
	if (Array.isArray(node)) {
		for (const x of node) walkClips(x, acc, playlists);
		return;
	}
	const obj = asRecord(node);
	if (!obj) return;
	if (obj.content_type === "clip" && asRecord(obj.content_item)) acc.push(obj.content_item);
	if (obj.entity_type === "song_schema" && obj.id && obj.title) acc.push(obj);
	const pid = String(obj.playlist_id || obj.feed_container_id || "");
	if (/^[0-9a-f-]{36}$/i.test(pid)) playlists.push(pid);
	for (const v of Object.values(obj)) walkClips(v, acc, playlists);
}
function normalize(raw, playlist) {
	const id = String(raw.id || "");
	const title = String(raw.title || "").trim();
	if (!id || !title) return null;
	const meta = asRecord(raw.metadata) ?? {};
	const tags = String(meta.tags || raw.display_tags || "").trim();
	const displayTags = String(raw.display_tags || tags).trim();
	const prompt = String(meta.prompt || "");
	return {
		id,
		title,
		handle: String(raw.handle || ""),
		displayName: String(raw.display_name || raw.handle || ""),
		playCount: Number(raw.play_count || 0),
		upvoteCount: Number(raw.upvote_count || 0),
		tags,
		displayTags,
		prompt: looksLikeCover(title) ? "" : prompt,
		imageUrl: String(raw.image_url || raw.image_large_url || ""),
		duration: Number(meta.duration || 0),
		playlist
	};
}
async function playlistSongs(id) {
	const out = [];
	for (const page of [1, 2]) try {
		const data = await getJson(PLAYLIST(id, page));
		const rows = Array.isArray(data.playlist_clips) ? data.playlist_clips : [];
		for (const row of rows) {
			const clip = asRecord(asRecord(row)?.clip) ?? asRecord(row);
			if (!clip) continue;
			const song = normalize(clip, String(data.name || id));
			if (song) out.push(song);
		}
		const total = Number(data.num_total_results || out.length);
		if (out.length >= total || rows.length === 0) break;
	} catch {
		break;
	}
	return out;
}
function learn(songs) {
	const weights = /* @__PURE__ */ new Map();
	const sections = /* @__PURE__ */ new Map();
	for (const s of songs) {
		const w = Math.log10(2 + s.playCount) + s.upvoteCount / 400;
		const bag = `${s.displayTags}, ${s.tags}`.split(/[,;/|]+/);
		for (const raw of bag) {
			const tag = raw.trim().toLowerCase();
			if (tag.length < 2 || tag.length > 40) continue;
			weights.set(tag, (weights.get(tag) ?? 0) + w);
		}
		for (const m of s.prompt.matchAll(/\[([^\]\n]{2,40})\]/g)) {
			const tag = m[1].split(/[: ,]/)[0]?.toLowerCase() ?? "";
			if (!tag) continue;
			sections.set(tag, (sections.get(tag) ?? 0) + 1);
		}
	}
	const topTags = [...weights.entries()].sort((a, b) => b[1] - a[1]).slice(0, 40).map(([tag, weight]) => ({
		tag,
		weight: Number(weight.toFixed(2))
	}));
	const sectionHabits = [...sections.entries()].sort((a, b) => b[1] - a[1]).slice(0, 16).map(([tag, count]) => ({
		tag,
		count
	}));
	const topSongs = [...songs].sort((a, b) => b.playCount + b.upvoteCount * 40 - (a.playCount + a.upvoteCount * 40)).slice(0, 48);
	return {
		pulledAt: Date.now(),
		songCount: songs.length,
		topTags,
		topSongs,
		sectionHabits
	};
}
var memory = null;
async function persist(learnData) {
	memory = learnData;
	try {
		await fetch(`${FOUNDRY}/trending`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(learnData),
			signal: AbortSignal.timeout(8e3)
		});
	} catch {}
}
async function loadPersisted() {
	if (memory) return memory;
	try {
		const json = await (await fetch(`${FOUNDRY}/trending`, { signal: AbortSignal.timeout(4e3) })).json();
		if (json.learn?.topSongs) {
			memory = json.learn;
			return memory;
		}
	} catch {}
	return memory;
}
async function pullTrendingCatalog() {
	const home = await postJson(HOME, { cursor: null });
	const clips = [];
	const playlistIds = [];
	walkClips(home, clips, playlistIds);
	const uniquePlaylists = [...new Set(playlistIds)].slice(0, 8);
	const fromLists = await Promise.all(uniquePlaylists.map((id) => playlistSongs(id)));
	const byId = /* @__PURE__ */ new Map();
	for (const raw of clips) {
		const song = normalize(raw);
		if (song) byId.set(song.id, song);
	}
	for (const list of fromLists) for (const song of list) {
		const prev = byId.get(song.id);
		byId.set(song.id, prev ? {
			...prev,
			...song,
			prompt: song.prompt || prev.prompt,
			displayTags: song.displayTags || prev.displayTags
		} : song);
	}
	const learned = learn([...byId.values()]);
	await persist(learned);
	return learned;
}
var getTrendingLearn_createServerFn_handler = createServerRpc({
	id: "f478ff78d7312f6d550081b556e53a2a3f466fba939408e9827bbf38b540440c",
	name: "getTrendingLearn",
	filename: "src/lib/suno/trending.ts"
}, (opts) => getTrendingLearn.__executeServer(opts));
var getTrendingLearn = createServerFn({ method: "GET" }).handler(getTrendingLearn_createServerFn_handler, async () => {
	return loadPersisted();
});
var pullSunoTrending_createServerFn_handler = createServerRpc({
	id: "52d13663e92f951a7e84866dcbb607673741a9a2590dd2ef607e62e4bdc4c3d4",
	name: "pullSunoTrending",
	filename: "src/lib/suno/trending.ts"
}, (opts) => pullSunoTrending.__executeServer(opts));
var pullSunoTrending = createServerFn({ method: "POST" }).handler(pullSunoTrending_createServerFn_handler, async () => {
	try {
		return {
			ok: true,
			learn: await pullTrendingCatalog()
		};
	} catch (err) {
		const cached = await loadPersisted();
		return {
			ok: false,
			error: err instanceof Error ? err.message : "Could not reach Suno",
			learn: cached
		};
	}
});
var ingestTrending_createServerFn_handler = createServerRpc({
	id: "ba3d901cde197839234a1f944f5dd303b28e1b84eb948f8b7469f0e8c469706d",
	name: "ingestTrending",
	filename: "src/lib/suno/trending.ts"
}, (opts) => ingestTrending.__executeServer(opts));
var ingestTrending = createServerFn({ method: "POST" }).handler(ingestTrending_createServerFn_handler, async () => {
	const learnData = memory ?? await loadPersisted();
	if (!learnData?.topSongs.length) return {
		ok: false,
		error: "Pull trending first.",
		ingested: 0,
		skipped: 0
	};
	try {
		const res = await fetch(`${FOUNDRY}/ingest-batch`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ songs: learnData.topSongs.map((s) => ({
				title: s.title,
				text: s.prompt,
				style: s.displayTags || s.tags,
				plays: s.playCount
			})) }),
			signal: AbortSignal.timeout(6e4)
		});
		const json = await res.json();
		if (!res.ok || !json.ok) return {
			ok: false,
			error: json.error || "Foundry ingest failed",
			ingested: json.ingested ?? 0,
			skipped: json.skipped ?? 0
		};
		return {
			ok: true,
			ingested: json.ingested ?? 0,
			skipped: json.skipped ?? 0
		};
	} catch {
		return {
			ok: false,
			error: "Foundry is warming up.",
			ingested: 0,
			skipped: 0
		};
	}
});
//#endregion
export { getTrendingLearn_createServerFn_handler, ingestTrending_createServerFn_handler, pullSunoTrending_createServerFn_handler };
