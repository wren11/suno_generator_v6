import { t as createServerFn } from "./ssr.mjs";
import { t as createServerRpc } from "./createServerRpc-A6pJPYTF.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/foundry-rYchyaVG.js
var FOUNDRY = "http://127.0.0.1:8099";
async function foundryFetch(path, init, timeoutMs = 2e4) {
	try {
		const res = await fetch(`${FOUNDRY}${path}`, {
			...init,
			signal: AbortSignal.timeout(timeoutMs)
		});
		const data = await res.json().catch(() => null) ?? {};
		if (!res.ok) return {
			ok: false,
			error: data.error || `Foundry ${res.status}`,
			data
		};
		return {
			ok: true,
			data
		};
	} catch {
		return {
			ok: false,
			error: "Foundry is warming up.",
			data: {}
		};
	}
}
function emptyExtract() {
	return {
		title: "",
		sections: [],
		rhyme_schema: "",
		energy: "",
		masculine_endings: 0,
		feminine_endings: 0,
		line_count: 0,
		meter_map: []
	};
}
function emptyGuide() {
	return {
		passed: 0,
		total: 0,
		score: 0,
		checks: []
	};
}
var foundryStatus_createServerFn_handler = createServerRpc({
	id: "2b64a99d117e9b0246e74bc9d6a3847b87fdf0cd7aeb6505953990e626ae4ce3",
	name: "foundryStatus",
	filename: "src/lib/suno/foundry.ts"
}, (opts) => foundryStatus.__executeServer(opts));
var foundryStatus = createServerFn({ method: "GET" }).handler(foundryStatus_createServerFn_handler, async () => {
	const res = await foundryFetch("/status", void 0, 4e3);
	if (!res.ok) return {
		ok: false,
		phase: "offline",
		training: false,
		trained: false,
		error: res.error
	};
	const d = res.data;
	return {
		ok: true,
		ready: Boolean(d.ready),
		phase: d.phase ?? "idle",
		training: Boolean(d.training),
		trained: Boolean(d.trained || d.ready),
		step: d.step ?? 0,
		steps: d.steps ?? 0,
		loss: typeof d.loss === "number" ? d.loss : null,
		avg: d.avg,
		params: d.params,
		examples: d.examples,
		error: d.error ?? null,
		elapsed: d.elapsed
	};
});
var foundryMetrics_createServerFn_handler = createServerRpc({
	id: "73fe173ac1682dbb15574a7d947ae9172a75a88565a194da43983d5d5fb36651",
	name: "foundryMetrics",
	filename: "src/lib/suno/foundry.ts"
}, (opts) => foundryMetrics.__executeServer(opts));
var foundryMetrics = createServerFn({ method: "GET" }).handler(foundryMetrics_createServerFn_handler, async () => {
	const res = await foundryFetch("/metrics", void 0, 4e3);
	const points = (res.data.points ?? []).map((p) => ({
		step: p.step ?? 0,
		loss: p.loss ?? 0,
		avg: p.avg ?? 0
	}));
	if (!res.ok) return {
		ok: false,
		points,
		error: res.error
	};
	return {
		ok: true,
		points
	};
});
var foundryExtract_createServerFn_handler = createServerRpc({
	id: "5d71f32bf0d2f1ed9534ad48fc210f3cfc7cf9bf9ee2bba68292908af880a817",
	name: "foundryExtract",
	filename: "src/lib/suno/foundry.ts"
}, (opts) => foundryExtract.__executeServer(opts));
var foundryExtract = createServerFn({ method: "POST" }).validator((input) => input).handler(foundryExtract_createServerFn_handler, async ({ data }) => {
	const res = await foundryFetch("/extract", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(data)
	}, 2e4);
	if (!res.ok) return {
		ok: false,
		error: res.error,
		extract: emptyExtract(),
		guide: emptyGuide()
	};
	return {
		ok: true,
		extract: res.data.extract ?? emptyExtract(),
		guide: res.data.guide ?? emptyGuide(),
		error: ""
	};
});
var foundryIngest_createServerFn_handler = createServerRpc({
	id: "c3ae3db948c376fa4a9ca75c4f32f9d33e85b3076e42234ca46ab5298154aafd",
	name: "foundryIngest",
	filename: "src/lib/suno/foundry.ts"
}, (opts) => foundryIngest.__executeServer(opts));
var foundryIngest = createServerFn({ method: "POST" }).validator((input) => input).handler(foundryIngest_createServerFn_handler, async ({ data }) => {
	const res = await foundryFetch("/ingest", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(data)
	}, 2e4);
	if (!res.ok) return {
		ok: false,
		error: res.error,
		extract: emptyExtract(),
		count: 0
	};
	return {
		ok: true,
		extract: res.data.extract ?? emptyExtract(),
		count: res.data.count ?? 0,
		error: ""
	};
});
var foundryTrain_createServerFn_handler = createServerRpc({
	id: "d0dcc8808cf0303c1f692df633919e88f5c21b3b8248c82cbd23ad7595446896",
	name: "foundryTrain",
	filename: "src/lib/suno/foundry.ts"
}, (opts) => foundryTrain.__executeServer(opts));
var foundryTrain = createServerFn({ method: "POST" }).validator((input) => input).handler(foundryTrain_createServerFn_handler, async ({ data }) => {
	const res = await foundryFetch("/train", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(data)
	}, 15e3);
	if (!res.ok) return {
		ok: false,
		error: res.error,
		already: false,
		started: false
	};
	return {
		ok: true,
		already: Boolean(res.data.already),
		started: Boolean(res.data.started),
		error: ""
	};
});
var foundryEval_createServerFn_handler = createServerRpc({
	id: "d52fe64db44bc5031895c1a561501656eb63931ad9cd96c8aa2b42336541099f",
	name: "foundryEval",
	filename: "src/lib/suno/foundry.ts"
}, (opts) => foundryEval.__executeServer(opts));
var foundryEval = createServerFn({ method: "POST" }).validator((input) => input).handler(foundryEval_createServerFn_handler, async ({ data }) => {
	const res = await foundryFetch("/eval", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(data)
	}, 18e4);
	const raw = res.data.model;
	const model = {
		ok: Boolean(raw?.ok),
		average: raw?.average ?? 0,
		error: raw?.error ?? "",
		reports: (raw?.reports ?? []).map((r) => ({
			theme: r.theme,
			passed: r.passed,
			total: r.total,
			score: r.score
		}))
	};
	if (!res.ok) return {
		ok: false,
		error: res.error,
		gold: emptyGuide(),
		model
	};
	return {
		ok: true,
		gold: res.data.gold ?? emptyGuide(),
		model,
		error: ""
	};
});
var foundryExport_createServerFn_handler = createServerRpc({
	id: "ef96ec4987941cf8285212f8bde7792bba50860bb9f6ded6de2d2ae572279840",
	name: "foundryExport",
	filename: "src/lib/suno/foundry.ts"
}, (opts) => foundryExport.__executeServer(opts));
var foundryExport = createServerFn({ method: "GET" }).handler(foundryExport_createServerFn_handler, async () => {
	const res = await foundryFetch("/export", void 0, 6e4);
	const files = res.data.files ?? [];
	if (!res.ok) return {
		ok: false,
		error: res.error,
		files,
		tokenizer: false
	};
	return {
		ok: Boolean(res.data.ok),
		files,
		tokenizer: Boolean(res.data.tokenizer),
		error: ""
	};
});
//#endregion
export { foundryEval_createServerFn_handler, foundryExport_createServerFn_handler, foundryExtract_createServerFn_handler, foundryIngest_createServerFn_handler, foundryMetrics_createServerFn_handler, foundryStatus_createServerFn_handler, foundryTrain_createServerFn_handler };
