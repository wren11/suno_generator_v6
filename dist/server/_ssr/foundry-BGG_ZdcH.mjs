import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { _ as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { s as require_jsx_runtime } from "../_libs/@radix-ui/react-collection+[...].mjs";
import { t as createServerFn } from "./ssr.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { i as pullSunoTrending, n as ingestTrending, t as getTrendingLearn } from "./trending-D4NJZGP2.mjs";
import { a as ScanLine, n as Upload, s as Radio, u as FlaskConical } from "../_libs/lucide-react.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { n as cn } from "./router-fI3E7ogk.mjs";
import { a as JobPulse, c as Textarea, f as useElapsed, i as Input, l as formatElapsed, n as BusyButton, o as Label, r as Button, t as Badge, u as foundryPhase } from "./job-pulse-B_PHw_Ru.mjs";
import { a as CartesianGrid, i as Line, n as YAxis, o as ResponsiveContainer, r as XAxis, s as Tooltip, t as LineChart } from "../_libs/recharts+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/foundry-BGG_ZdcH.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var foundryStatus = createServerFn({ method: "GET" }).handler(createSsrRpc("2b64a99d117e9b0246e74bc9d6a3847b87fdf0cd7aeb6505953990e626ae4ce3"));
var foundryMetrics = createServerFn({ method: "GET" }).handler(createSsrRpc("73fe173ac1682dbb15574a7d947ae9172a75a88565a194da43983d5d5fb36651"));
var foundryExtract = createServerFn({ method: "POST" }).validator((input) => input).handler(createSsrRpc("5d71f32bf0d2f1ed9534ad48fc210f3cfc7cf9bf9ee2bba68292908af880a817"));
var foundryIngest = createServerFn({ method: "POST" }).validator((input) => input).handler(createSsrRpc("c3ae3db948c376fa4a9ca75c4f32f9d33e85b3076e42234ca46ab5298154aafd"));
var foundryTrain = createServerFn({ method: "POST" }).validator((input) => input).handler(createSsrRpc("d0dcc8808cf0303c1f692df633919e88f5c21b3b8248c82cbd23ad7595446896"));
var foundryEval = createServerFn({ method: "POST" }).validator((input) => input).handler(createSsrRpc("d52fe64db44bc5031895c1a561501656eb63931ad9cd96c8aa2b42336541099f"));
var foundryExport = createServerFn({ method: "GET" }).handler(createSsrRpc("ef96ec4987941cf8285212f8bde7792bba50860bb9f6ded6de2d2ae572279840"));
var STEPS = [
	{
		id: "extract",
		label: "Extract",
		blurb: "Feet, rhyme, sections from original lyrics"
	},
	{
		id: "tokenize",
		label: "Tokenize",
		blurb: "GPT-2 BPE via Hugging Face AutoTokenizer"
	},
	{
		id: "train",
		label: "Train",
		blurb: "Fine-tune distilgpt2 on original lyric verses"
	},
	{
		id: "eval",
		label: "Eval",
		blurb: "MasterofSFL guide checks on LM sheets"
	},
	{
		id: "export",
		label: "Export",
		blurb: "Hugging Face folder, model card, safetensors"
	},
	{
		id: "ready",
		label: "Serve",
		blurb: "Loopback inference sidecar"
	}
];
function FoundryDesk() {
	const [status, setStatus] = (0, import_react.useState)({
		ok: false,
		phase: "offline"
	});
	const [points, setPoints] = (0, import_react.useState)([]);
	const [title, setTitle] = (0, import_react.useState)("");
	const [lyrics, setLyrics] = (0, import_react.useState)("");
	const [extract, setExtract] = (0, import_react.useState)(null);
	const [checks, setChecks] = (0, import_react.useState)([]);
	const [evalReport, setEvalReport] = (0, import_react.useState)("");
	const [files, setFiles] = (0, import_react.useState)([]);
	const [busy, setBusy] = (0, import_react.useState)(null);
	const [steps, setSteps] = (0, import_react.useState)(300);
	const [trending, setTrending] = (0, import_react.useState)(null);
	const [startedAt, setStartedAt] = (0, import_react.useState)(void 0);
	const liveKind = busy ?? (status.training ? "train" : null);
	const localElapsed = useElapsed(Boolean(busy), startedAt);
	const elapsedMs = busy ? localElapsed : Math.round((status.elapsed ?? 0) * 1e3);
	const trainProgress = status.training && status.steps ? Math.min(1, (status.step ?? 0) / Math.max(1, status.steps)) : void 0;
	function begin(kind) {
		setStartedAt(Date.now());
		setBusy(kind);
	}
	(0, import_react.useEffect)(() => {
		let timer = 0;
		let cancelled = false;
		async function tick() {
			const s = await foundryStatus();
			if (cancelled) return;
			setStatus(s);
			if (s.training || s.step && s.step > 0) {
				const m = await foundryMetrics();
				if (!cancelled && m.points.length) setPoints(m.points);
			}
			timer = window.setTimeout(tick, s.training ? 800 : 4e3);
		}
		tick();
		getTrendingLearn().then((l) => {
			if (!cancelled && l) setTrending(l);
		});
		return () => {
			cancelled = true;
			window.clearTimeout(timer);
		};
	}, []);
	const phase = status.phase || "offline";
	const activeIndex = STEPS.findIndex((s) => s.id === phase);
	const chart = (0, import_react.useMemo)(() => points.map((p) => ({
		step: p.step,
		loss: Number(p.loss.toFixed(3)),
		avg: p.avg ? Number(p.avg.toFixed(3)) : void 0
	})), [points]);
	async function runExtract() {
		if (lyrics.trim().length < 12) {
			toast("Paste original lyrics first");
			return;
		}
		begin("extract");
		const t0 = Date.now();
		try {
			const res = await foundryExtract({ data: {
				text: lyrics,
				title
			} });
			const took = formatElapsed(Date.now() - t0);
			if (!res.ok) {
				toast("Extract failed", { description: `${res.error} · ${took}` });
				return;
			}
			setExtract(res.extract);
			setChecks(res.guide.checks ?? []);
			toast("Meter read", { description: `${res.extract.line_count} lines · ${res.extract.rhyme_schema || "free rhyme"} · ${took}` });
		} finally {
			setBusy(null);
		}
	}
	async function runIngest() {
		if (lyrics.trim().length < 12) return;
		begin("ingest");
		const t0 = Date.now();
		try {
			const res = await foundryIngest({ data: {
				text: lyrics,
				title
			} });
			const took = formatElapsed(Date.now() - t0);
			if (!res.ok) {
				toast("Could not ingest", { description: `${res.error} · ${took}` });
				return;
			}
			toast("Ingested", { description: `${res.count ?? 0} extracts queued · ${took}` });
		} finally {
			setBusy(null);
		}
	}
	async function runTrain() {
		begin("train");
		try {
			const res = await foundryTrain({ data: {
				steps,
				corpus_n: 640
			} });
			if (!res.ok) {
				toast("Could not start training", { description: res.error });
				return;
			}
			toast(res.already ? "Already training" : "Training started", { description: `${steps} steps · watch loss tick on this page.` });
		} finally {
			setBusy(null);
		}
	}
	async function runEval() {
		begin("eval");
		const t0 = Date.now();
		try {
			const res = await foundryEval({ data: { n: 3 } });
			const took = formatElapsed(Date.now() - t0);
			if (!res.ok) {
				toast("Eval failed", { description: `${res.error} · ${took}` });
				return;
			}
			const gold = res.gold;
			const model = res.model;
			const goldLine = gold ? `Gold compiler ${gold.passed}/${gold.total} (${Math.round((gold.score ?? 0) * 100)}%).` : "";
			const modelLine = model.ok ? ` Weights average ${Math.round((model.average ?? 0) * 100)}%.` : ` Weights: ${model.error || "not trained yet"}.`;
			setEvalReport(`${goldLine}${modelLine} · ${took}`);
			toast("Eval finished", { description: `${goldLine}${modelLine} · ${took}` });
		} finally {
			setBusy(null);
		}
	}
	async function runExport() {
		begin("export");
		const t0 = Date.now();
		try {
			const res = await foundryExport();
			const took = formatElapsed(Date.now() - t0);
			setFiles(res.files ?? []);
			toast(res.ok ? "Export ready" : "Export incomplete", { description: `${res.ok ? `${res.files.length} files written` : res.error} · ${took}` });
		} finally {
			setBusy(null);
		}
	}
	async function runPull() {
		begin("pull");
		const t0 = Date.now();
		try {
			const res = await pullSunoTrending();
			const took = formatElapsed(Date.now() - t0);
			if (res.learn) setTrending(res.learn);
			toast(res.ok ? `Pulled ${res.learn.songCount} live Suno songs` : "Using cached catalog", { description: res.ok ? `${res.learn.topTags.slice(0, 5).map((t) => t.tag).join(", ")} · ${took}` : `${res.error} · ${took}` });
		} finally {
			setBusy(null);
		}
	}
	async function runBulkTrain() {
		begin("bulk");
		const t0 = Date.now();
		try {
			const ing = await ingestTrending();
			if (!ing.ok) {
				toast("Could not ingest trending", { description: `${ing.error} · ${formatElapsed(Date.now() - t0)}` });
				return;
			}
			const res = await foundryTrain({ data: {
				steps,
				corpus_n: 640
			} });
			toast(res.ok ? `Ingested ${ing.ingested}, training started` : "Ingested but train did not start", { description: `${ing.skipped} skipped · ${formatElapsed(Date.now() - t0)}` });
		} finally {
			setBusy(null);
		}
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "min-h-dvh text-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
			className: "sticky top-0 z-30 border-b bg-card/85 backdrop-blur-md",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex min-w-0 flex-1 items-center gap-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "grid size-10 shrink-0 place-items-center rounded-lg bg-ink text-card shadow-[var(--shadow-border)]",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FlaskConical, { className: "size-5" })
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "min-w-0",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "font-display text-2xl leading-none tracking-tight",
								children: "Foundry"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1 hidden text-sm text-muted-foreground sm:block",
								children: "Scansion-LM · extract → tokenize → train → eval → Hugging Face"
							})]
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						variant: status.ok ? "default" : "outline",
						className: cn(liveKind && "animate-pulse"),
						children: status.training ? `train ${status.step ?? 0}/${status.steps ?? steps}` : busy ? `${busy} · ${formatElapsed(elapsedMs)}` : status.ok ? phase : "offline"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						type: "button",
						variant: "ghost",
						size: "sm",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/",
							children: "Studio"
						})
					})
				]
			}), liveKind ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(JobPulse, {
				title: foundryPhase(liveKind, elapsedMs),
				detail: status.training ? status.phase : busy ?? void 0,
				elapsedMs,
				progress: liveKind === "train" ? trainProgress : void 0,
				stats: [
					status.training && status.step != null ? `step ${status.step}/${status.steps ?? steps}` : "",
					status.loss != null ? `loss ${status.loss.toFixed(3)}` : "",
					status.examples ? `${status.examples} blocks` : "",
					trending && busy === "pull" ? `${trending.songCount} cached` : ""
				].filter(Boolean)
			}) : null]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto grid max-w-7xl gap-8 px-4 py-8 sm:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-8",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "kicker",
							children: "Pipeline"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h1", {
							className: "mt-2 font-display text-3xl leading-tight tracking-tight",
							children: ["Train our own lyric model.", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "italic text-ink",
								children: " Original extracts only."
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-3 max-w-prose text-sm text-muted-foreground",
							children: "Hit DNA is form — meters, rhyme, production language — never copyrighted Billboard lyrics. Pull live Suno charts for tag language and public Custom Mode prompts, then bulk-train on those extracts."
						})
					] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
						className: "paper space-y-3 rounded-xl p-4",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "kicker",
								children: "Suno trending"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm text-muted-foreground",
								children: "Reads Suno’s public homepage and curated playlists. Learns display tags and structure from high play-count clips. Public prompts only — known hit titles are skipped."
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
									type: "button",
									busy: busy === "pull",
									disabled: Boolean(busy),
									idle: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Radio, { className: "size-4" }), "Pull trending"] }),
									pending: `Pulling · ${formatElapsed(elapsedMs)}`,
									onClick: () => void runPull()
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
									type: "button",
									variant: "outline",
									busy: busy === "bulk",
									disabled: Boolean(busy) || !trending || status.training,
									idle: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FlaskConical, { className: "size-4" }), "Ingest + train"] }),
									pending: `Ingesting · ${formatElapsed(elapsedMs)}`,
									onClick: () => void runBulkTrain()
								})]
							}),
							busy === "pull" ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "text-sm text-muted-foreground",
								children: [
									foundryPhase("pull", elapsedMs),
									" · ",
									formatElapsed(elapsedMs)
								]
							}) : null,
							trending ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
										className: "font-mono text-xs text-muted-foreground",
										children: [
											trending.songCount,
											" songs · ",
											new Date(trending.pulledAt).toLocaleString()
										]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "flex flex-wrap gap-1.5",
										children: trending.topTags.slice(0, 14).map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
											className: "rounded-full bg-secondary px-2.5 py-1 text-xs text-secondary-foreground",
											children: t.tag
										}, t.tag))
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
										className: "space-y-1",
										children: trending.topSongs.slice(0, 6).map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
											className: "flex items-baseline justify-between gap-3 text-sm",
											children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
												className: "truncate font-medium",
												children: s.title
											}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
												className: "shrink-0 font-mono text-xs tabular-nums text-muted-foreground",
												children: [s.playCount.toLocaleString(), " plays"]
											})]
										}, s.id))
									})
								]
							}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm text-muted-foreground",
								children: "No catalog yet. Pull to learn what is working on Suno right now."
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("ol", {
						className: "space-y-2",
						children: STEPS.map((s, i) => {
							const on = s.id === phase || phase === "corpus" && s.id === "extract";
							const done = activeIndex > i || phase === "ready";
							return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
								className: cn("barline rounded-lg px-3 py-3", on ? "bg-secondary" : "paper"),
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-baseline justify-between gap-3",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
										className: "font-medium",
										children: [
											/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
												className: "font-mono text-xs text-muted-foreground",
												children: ["0", i + 1]
											}),
											" ",
											s.label
										]
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "kicker",
										children: on ? status.training ? `${status.step ?? 0}/${status.steps ?? 0}` : "now" : done ? "done" : ""
									})]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "mt-1 text-sm text-muted-foreground",
									children: s.blurb
								})]
							}, s.id);
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
						className: "space-y-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "kicker",
								children: "Train"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex flex-wrap items-end gap-3",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "space-y-1",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
											htmlFor: "steps",
											children: "Steps"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
											id: "steps",
											type: "number",
											min: 40,
											max: 800,
											value: steps,
											onChange: (e) => setSteps(Number(e.target.value) || 200),
											className: "w-28"
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
										type: "button",
										busy: busy === "train" || Boolean(status.training),
										disabled: Boolean(busy) || status.training,
										idle: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FlaskConical, { className: "size-4" }), "Start training"] }),
										pending: status.training ? `Step ${status.step ?? 0}/${status.steps ?? steps} · ${formatElapsed(elapsedMs)}` : `Starting · ${formatElapsed(elapsedMs)}`,
										onClick: () => void runTrain()
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
										type: "button",
										variant: "outline",
										busy: busy === "eval",
										disabled: Boolean(busy) || status.training,
										idle: "Eval guide",
										pending: `Eval · ${formatElapsed(elapsedMs)}`,
										onClick: () => void runEval()
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
										type: "button",
										variant: "outline",
										busy: busy === "export",
										disabled: Boolean(busy) || status.training,
										idle: "Export HF",
										pending: `Export · ${formatElapsed(elapsedMs)}`,
										onClick: () => void runExport()
									})
								]
							}),
							status.loss != null ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "font-mono text-xs text-muted-foreground",
								children: [
									"loss ",
									status.loss.toFixed(3),
									status.params ? ` · ${(status.params / 1e6).toFixed(1)}M params` : "",
									status.examples ? ` · ${status.examples} lyric blocks` : ""
								]
							}) : null,
							status.error ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm text-destructive",
								children: status.error
							}) : null,
							evalReport ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm text-muted-foreground",
								children: evalReport
							}) : null
						]
					})
				]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-8",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
						className: "space-y-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "kicker",
							children: "Loss"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "paper h-48 rounded-xl p-3",
							children: chart.length > 1 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
								width: "100%",
								height: "100%",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(LineChart, {
									data: chart,
									margin: {
										top: 8,
										right: 8,
										left: 0,
										bottom: 0
									},
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CartesianGrid, {
											stroke: "var(--color-staff)",
											vertical: false
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
											dataKey: "step",
											tick: {
												fill: "var(--color-muted-foreground)",
												fontSize: 11
											},
											axisLine: false,
											tickLine: false
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(YAxis, {
											tick: {
												fill: "var(--color-muted-foreground)",
												fontSize: 11
											},
											axisLine: false,
											tickLine: false,
											width: 36
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Tooltip, {
											contentStyle: {
												background: "var(--color-card)",
												border: "1px solid var(--color-border)",
												borderRadius: 8
											},
											labelStyle: { color: "var(--color-muted-foreground)" }
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Line, {
											type: "monotone",
											dataKey: "loss",
											stroke: "var(--color-primary)",
											dot: false,
											strokeWidth: 2
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Line, {
											type: "monotone",
											dataKey: "avg",
											stroke: "var(--color-ink)",
											dot: false,
											strokeWidth: 1.6
										})
									]
								})
							}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "flex h-full items-center justify-center text-sm text-muted-foreground",
								children: "Loss appears once training writes a step."
							})
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
						className: "space-y-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "kicker",
								children: "Extract an original"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm text-muted-foreground",
								children: "Paste lyrics you wrote. Do not paste copyrighted hit lyrics — the foundry will refuse to be a clone mill."
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "ex-title",
									children: "Title"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									id: "ex-title",
									value: title,
									onChange: (e) => setTitle(e.target.value),
									placeholder: "Working title"
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "ex-lyrics",
									children: "Lyrics"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
									id: "ex-lyrics",
									value: lyrics,
									onChange: (e) => setLyrics(e.target.value),
									placeholder: "[Verse 1]\nYour lines here\n\n[Chorus]\nThe hook",
									className: "min-h-40 font-mono text-[13px]"
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
									type: "button",
									busy: busy === "extract",
									disabled: Boolean(busy),
									idle: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScanLine, { className: "size-4" }), "Read the meter"] }),
									pending: `Reading · ${formatElapsed(elapsedMs)}`,
									onClick: () => void runExtract()
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
									type: "button",
									variant: "outline",
									busy: busy === "ingest",
									disabled: Boolean(busy),
									idle: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Upload, { className: "size-4" }), "Add to next train"] }),
									pending: `Saving · ${formatElapsed(elapsedMs)}`,
									onClick: () => void runIngest()
								})]
							}),
							extract ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "paper space-y-2 rounded-xl p-4",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
										className: "font-display text-xl",
										children: extract.title || title || "Untitled extract"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
										className: "font-mono text-xs text-muted-foreground",
										children: [
											"rhyme ",
											extract.rhyme_schema || "—",
											" · ",
											extract.energy,
											" · ",
											extract.masculine_endings,
											" masc / ",
											extract.feminine_endings,
											" fem · ",
											extract.line_count,
											" lines"
										]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "flex flex-wrap gap-1.5",
										children: (extract.meter_map ?? []).map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, {
											variant: "outline",
											children: [
												m.section,
												": ",
												m.dominant_foot
											]
										}, m.section))
									})
								]
							}) : null,
							checks.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
								className: "space-y-1",
								children: checks.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
									className: "flex gap-2 text-sm",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: c.ok ? "text-foreground" : "text-destructive",
										children: c.ok ? "pass" : "fail"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "text-muted-foreground",
										children: c.note
									})]
								}, c.name))
							}) : null
						]
					}),
					files.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
						className: "space-y-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "kicker",
							children: "Hugging Face bundle"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
							className: "font-mono text-xs text-muted-foreground",
							children: files.map((f) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: f }, f))
						})]
					}) : null
				]
			})]
		})]
	});
}
function FoundryPage() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FoundryDesk, {});
}
//#endregion
export { FoundryPage as component };
