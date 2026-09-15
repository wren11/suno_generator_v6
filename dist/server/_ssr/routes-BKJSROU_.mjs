import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { _ as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { s as require_jsx_runtime } from "../_libs/@radix-ui/react-collection+[...].mjs";
import { t as createServerFn } from "./ssr.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { a as hitsById, i as hitMatchesFilter, n as HIT_GENRES, r as formatStreams, t as HITS } from "./hits-DKJ_Fcz3.mjs";
import { a as ScanLine, c as LoaderCircle, d as Download, f as Copy, g as BookOpen, h as Bookmark, i as Trash2, l as Library, m as Check, o as RefreshCw, p as ChevronDown, t as X, u as FlaskConical } from "../_libs/lucide-react.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { a as DialogOverlay, i as DialogDescription, n as DialogClose, o as DialogPortal, r as DialogContent, s as DialogTitle, t as Dialog } from "../_libs/@radix-ui/react-dialog+[...].mjs";
import { a as SelectItemIndicator, c as SelectTrigger$1, i as SelectItem$1, l as SelectValue$1, n as SelectContent$1, o as SelectItemText, r as SelectIcon, s as SelectPortal, t as Select$1, u as SelectViewport } from "../_libs/@radix-ui/react-select+[...].mjs";
import { n as cn } from "./router-fI3E7ogk.mjs";
import { a as JobPulse, c as Textarea, d as generatePhase, f as useElapsed, i as Input, l as formatElapsed, n as BusyButton, o as Label, r as Button, s as ProgressRail, t as Badge } from "./job-pulse-B_PHw_Ru.mjs";
import { a as PRESETS, c as STRUCTURES, d as VOCAL_RANGES, f as buildLiveStyle, g as sliderGuess, h as packageZip, i as METERLINES, l as TEMPO_MARKINGS, m as downloadBlob, n as FEET, o as PUNCTUATION_NOTES, r as GENRE_OPTIONS, s as RHYME_SCHEMAS, t as DEFAULT_COMPOSER, u as VOCAL_DELIVERIES } from "./local-style-DkcnWzaw.mjs";
import { i as SliderTrack, n as SliderRange, r as SliderThumb, t as Slider$1 } from "../_libs/radix-ui__react-slider.mjs";
import { n as SwitchThumb, t as Switch$1 } from "../_libs/radix-ui__react-switch.mjs";
import { n as create, t as persist } from "../_libs/zustand.mjs";
import { a as Viewport, i as ScrollAreaThumb, n as Root, r as ScrollAreaScrollbar, t as Corner } from "../_libs/radix-ui__react-scroll-area.mjs";
import { i as Trigger, n as List, r as Root2, t as Content } from "../_libs/radix-ui__react-tabs.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-BKJSROU_.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function HitDnaPicker({ selected, onChange }) {
	const [filter, setFilter] = (0, import_react.useState)("Now");
	const [q, setQ] = (0, import_react.useState)("");
	const list = (0, import_react.useMemo)(() => {
		const query = q.trim().toLowerCase();
		return HITS.filter((h) => hitMatchesFilter(h, filter)).filter((h) => {
			if (!query) return true;
			return `${h.title} ${h.artist} ${h.genres.join(" ")}`.toLowerCase().includes(query);
		});
	}, [filter, q]);
	function toggle(id) {
		if (selected.includes(id)) {
			onChange(selected.filter((x) => x !== id));
			return;
		}
		if (selected.length >= 3) {
			onChange([...selected.slice(1), id]);
			return;
		}
		onChange([...selected, id]);
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-end justify-between gap-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "kicker",
					children: "Hit DNA"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-1 text-sm text-muted-foreground",
					children: "Blend structure from chart records. Max 3. Lyrics stay original."
				})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
					className: "font-mono text-xs tabular-nums text-muted-foreground",
					children: [selected.length, "/3"]
				})]
			}),
			selected.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "flex flex-wrap gap-1.5",
				children: hitsById(selected).map((h) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					type: "button",
					onClick: () => toggle(h.id),
					className: "rounded-full bg-secondary px-2.5 py-1 text-xs text-secondary-foreground",
					children: h.title
				}, h.id))
			}) : null,
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
				value: q,
				onChange: (e) => setQ(e.target.value),
				placeholder: "Search title or artist",
				"aria-label": "Search hit DNA"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1",
				children: HIT_GENRES.map((g) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					type: "button",
					onClick: () => setFilter(g),
					className: cn("h-9 shrink-0 rounded-full px-3 text-xs font-medium transition-colors duration-150", filter === g ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"),
					children: g
				}, g))
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "max-h-64 space-y-1.5 overflow-y-auto pr-1",
				children: [list.map((hit) => {
					const on = selected.includes(hit.id);
					const streams = formatStreams(hit.streamsBn);
					return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
						type: "button",
						onClick: () => toggle(hit.id),
						className: cn("flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors duration-150", on ? "bg-secondary barline" : "hover:bg-muted"),
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: cn("mt-1 size-2 shrink-0 rounded-full", on ? "bg-primary" : "bg-border") }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
								className: "min-w-0 flex-1",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
									className: "flex items-baseline justify-between gap-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "truncate text-sm font-medium",
										children: hit.title
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "shrink-0 font-mono text-xs tabular-nums text-muted-foreground",
										children: streams ?? hit.year
									})]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
									className: "mt-0.5 block truncate text-xs text-muted-foreground",
									children: [
										hit.artist,
										" · ",
										hit.bpm,
										" BPM · ",
										hit.genres[0]
									]
								})]
							}),
							hit.trending ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
								variant: "outline",
								className: "mt-0.5 shrink-0",
								children: "Now"
							}) : null
						]
					}, hit.id);
				}), list.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "px-1 py-6 text-center text-sm text-muted-foreground",
					children: "No matches in this filter."
				}) : null]
			})
		]
	});
}
var Select = Select$1;
var SelectValue = SelectValue$1;
var SelectTrigger = import_react.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectTrigger$1, {
	ref,
	className: cn("flex h-11 w-full items-center justify-between gap-2 rounded-md bg-card px-3 text-sm shadow-[var(--shadow-border)] outline-none transition-[box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-ring/70 disabled:cursor-not-allowed disabled:opacity-50 data-[placeholder]:text-muted-foreground", className),
	...props,
	children: [children, /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectIcon, {
		asChild: true,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChevronDown, { className: "size-4 opacity-60" })
	})]
}));
SelectTrigger.displayName = SelectTrigger$1.displayName;
var SelectContent = import_react.forwardRef(({ className, children, position = "popper", ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectPortal, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent$1, {
	ref,
	className: cn("relative z-50 max-h-72 min-w-32 overflow-hidden rounded-lg bg-popover text-popover-foreground shadow-[var(--shadow-soft)]", position === "popper" && "data-[side=bottom]:translate-y-1", className),
	position,
	...props,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectViewport, {
		className: cn("p-1", position === "popper" && "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]"),
		children
	})
}) }));
SelectContent.displayName = SelectContent$1.displayName;
var SelectItem = import_react.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectItem$1, {
	ref,
	className: cn("relative flex w-full cursor-pointer select-none items-center rounded-md py-2 pl-8 pr-3 text-sm outline-none focus:bg-accent data-[disabled]:pointer-events-none data-[disabled]:opacity-50", className),
	...props,
	children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
		className: "absolute left-2 flex size-4 items-center justify-center",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItemIndicator, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "size-3.5" }) })
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItemText, { children })]
}));
SelectItem.displayName = SelectItem$1.displayName;
var Slider = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Slider$1, {
	ref,
	className: cn("relative flex w-full touch-none select-none items-center", className),
	...props,
	children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SliderTrack, {
		className: "relative h-2 w-full grow overflow-hidden rounded-full bg-muted",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SliderRange, { className: "absolute h-full bg-primary" })
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SliderThumb, { className: "block size-5 rounded-full bg-card shadow-[var(--shadow-border)] outline-none ring-2 ring-primary transition-transform duration-150 focus-visible:ring-2 focus-visible:ring-ring" })]
}));
Slider.displayName = Slider$1.displayName;
var Switch = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch$1, {
	className: cn("peer inline-flex h-6 w-10 shrink-0 cursor-pointer items-center rounded-full shadow-[var(--shadow-border)] transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-accent", className),
	...props,
	ref,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SwitchThumb, { className: cn("pointer-events-none block size-5 translate-x-0.5 rounded-full bg-foreground shadow-sm transition-transform duration-150 data-[state=checked]:translate-x-[18px] data-[state=checked]:bg-primary-foreground") })
}));
Switch.displayName = Switch$1.displayName;
var useStudio = create()(persist((set, get) => ({
	composer: DEFAULT_COMPOSER,
	patch: (partial) => set((s) => ({ composer: {
		...s.composer,
		...partial
	} })),
	reset: () => set({ composer: DEFAULT_COMPOSER }),
	current: null,
	setCurrent: (g) => set({ current: g }),
	library: [],
	saveCurrent: () => {
		const { current, library } = get();
		if (!current) return;
		set({ library: [current, ...library.filter((g) => g.id !== current.id)].slice(0, 40) });
	},
	remove: (id) => set((s) => ({
		library: s.library.filter((g) => g.id !== id),
		current: s.current?.id === id ? null : s.current
	})),
	load: (id) => {
		const g = get().library.find((x) => x.id === id);
		if (!g) return;
		set({
			current: g,
			composer: g.composer
		});
	}
}), {
	name: "scansion-studio",
	skipHydration: true,
	partialize: (s) => ({
		composer: s.composer,
		library: s.library,
		current: s.current
	})
}));
function Composer() {
	const composer = useStudio((s) => s.composer);
	const patch = useStudio((s) => s.patch);
	function setGenre(index, field, value) {
		const genres = composer.genres.map((g, i) => i === index ? {
			...g,
			[field]: value
		} : g);
		const total = genres.reduce((n, g) => n + Number(g.weight || 0), 0);
		if (field === "weight" && genres.length === 2) {
			const other = index === 0 ? 1 : 0;
			genres[other] = {
				...genres[other],
				weight: Math.max(0, 100 - Number(value))
			};
		}
		patch({ genres: total === 0 ? genres : genres });
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "space-y-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex flex-wrap gap-2",
						children: PRESETS.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							type: "button",
							onClick: () => patch({
								...DEFAULT_COMPOSER,
								...p.patch,
								genres: p.patch.genres.map((g) => ({
									name: g.name,
									weight: g.weight
								}))
							}),
							className: "rounded-full bg-accent px-3 py-2 text-xs font-semibold text-accent-foreground transition-colors duration-150 hover:bg-primary hover:text-primary-foreground",
							title: p.blurb,
							children: p.label
						}, p.id))
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
							htmlFor: "idea",
							children: "The story"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
							id: "idea",
							value: composer.idea,
							onChange: (e) => patch({ idea: e.target.value }),
							placeholder: "Who is speaking, what happened, what the song must make the listener feel. Specifics beat adjectives.",
							className: "min-h-32 font-display text-[15px] leading-relaxed"
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-3 sm:grid-cols-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
								htmlFor: "title",
								children: "Working title"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								id: "title",
								value: composer.title,
								onChange: (e) => patch({ title: e.target.value }),
								placeholder: "Leave blank to invent"
							})]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Point of view" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "grid grid-cols-3 gap-1 rounded-lg bg-muted p-1",
								children: [
									"first",
									"second",
									"third"
								].map((pov) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
									type: "button",
									onClick: () => patch({ pov }),
									className: cn("h-9 rounded-md text-xs font-medium capitalize transition-colors duration-150", composer.pov === pov ? "bg-card text-foreground shadow-[var(--shadow-border)]" : "text-muted-foreground"),
									children: pov
								}, pov))
							})]
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(HitDnaPicker, {
				selected: composer.hitIds,
				onChange: (hitIds) => patch({ hitIds })
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "space-y-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "kicker",
					children: "Genre blend"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-1 text-sm text-muted-foreground",
					children: "Percentages tell Suno which pocket wins."
				})] }), composer.genres.slice(0, 2).map((g, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between gap-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							value: g.name,
							onValueChange: (v) => setGenre(i, "name", v),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
								className: "flex-1",
								"aria-label": i === 0 ? "Primary genre" : "Blend genre",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: GENRE_OPTIONS.map((opt) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
								value: opt,
								children: opt
							}, opt)) })]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, {
							variant: "outline",
							className: "min-w-12 justify-center font-mono tabular-nums",
							children: [g.weight, "%"]
						})]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Slider, {
						min: 0,
						max: 100,
						step: 5,
						value: [g.weight],
						onValueChange: ([v]) => setGenre(i, "weight", v ?? 0),
						"aria-label": `${g.name} weight`
					})]
				}, i))]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "grid gap-4 sm:grid-cols-2",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Voice",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							value: composer.vocalGender,
							onValueChange: (v) => patch({ vocalGender: v }),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
								"aria-label": "Vocal gender",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "unspecified",
									children: "Unspecified"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "male",
									children: "Male"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "female",
									children: "Female"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "duet",
									children: "Duet"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "choir",
									children: "Choir"
								})
							] })]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Range",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							value: composer.vocalRange,
							onValueChange: (v) => patch({ vocalRange: v }),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
								"aria-label": "Vocal range",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: VOCAL_RANGES.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
								value: r,
								children: r
							}, r)) })]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-2 sm:col-span-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Delivery" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							value: composer.vocalDelivery,
							onValueChange: (v) => patch({ vocalDelivery: v }),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
								"aria-label": "Vocal delivery",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: VOCAL_DELIVERIES.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
								value: d,
								children: d
							}, d)) })]
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "space-y-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "kicker",
						children: "Pulse"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-4 sm:grid-cols-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Italian tempo",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: composer.tempo,
									onValueChange: (v) => patch({ tempo: v }),
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
										"aria-label": "Tempo marking",
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: TEMPO_MARKINGS.map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
										value: t.name,
										children: t.name
									}, t.name)) })]
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: `BPM ${composer.bpm}`,
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "flex h-11 items-center px-1",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Slider, {
										min: 60,
										max: 200,
										step: 1,
										value: [composer.bpm],
										onValueChange: ([v]) => patch({ bpm: v ?? 120 })
									})
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Signature",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: composer.timeSignature,
									onValueChange: (v) => patch({ timeSignature: v }),
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
										"aria-label": "Time signature",
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: [
										"4/4",
										"3/4",
										"6/8",
										"12/8",
										"5/4"
									].map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
										value: s,
										children: s
									}, s)) })]
								})
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-2",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex items-center justify-between",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Vocal aggression" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-mono text-xs tabular-nums text-muted-foreground",
									children: composer.energy
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Slider, {
								min: 0,
								max: 100,
								step: 1,
								value: [composer.energy],
								onValueChange: ([v]) => patch({ energy: v ?? 50 })
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Low = pyrrhic / feminine rhyme. High = spondee / gallop / masculine lock."
							})
						]
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "grid gap-4 sm:grid-cols-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
					label: "Form",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
						value: composer.structure,
						onValueChange: (v) => patch({ structure: v }),
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
							"aria-label": "Song structure",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: STRUCTURES.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
							value: s.id,
							children: s.label
						}, s.id)) })]
					})
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
					label: "Rhyme schema",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
						value: composer.rhyme,
						onValueChange: (v) => patch({ rhyme: v }),
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
							"aria-label": "Rhyme schema",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: RHYME_SCHEMAS.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
							value: r.id,
							children: r.label
						}, r.id)) })]
					})
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "paper space-y-3 rounded-xl p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ToggleRow, {
						label: "Stagger meters",
						hint: "Alternate feet between lines so Suno does not flatten into AABB rap.",
						checked: composer.meterStagger,
						onChange: (meterStagger) => patch({ meterStagger })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ToggleRow, {
						label: "Breath lines",
						hint: "Blank lines for fills and vocal reset — the largest punctuation lever.",
						checked: composer.extraBreaks,
						onChange: (extraBreaks) => patch({ extraBreaks })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ToggleRow, {
						label: "Call and response",
						hint: "Writes the style cue and metatags Suno needs for consistent answers.",
						checked: composer.callAndResponse,
						onChange: (callAndResponse) => patch({ callAndResponse })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between gap-3 pt-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Suno target" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							value: composer.sunoVersion,
							onValueChange: (v) => patch({ sunoVersion: v }),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
								className: "w-36",
								"aria-label": "Suno version",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "v6",
									children: "v6 hawk"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "v6-wild",
									children: "v6 wild"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "v6-mini",
									children: "v6 mini"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "v5.5",
									children: "v5.5"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "v5",
									children: "v5"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "v4.5",
									children: "v4.5"
								})
							] })]
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between gap-3 pt-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm font-medium",
							children: "Payload budget"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-0.5 text-xs text-muted-foreground",
							children: "5k lyrics for v6 Custom Mode. 3k for compact / older paste."
						})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "grid grid-cols-2 gap-1 rounded-lg bg-muted p-1",
							children: ["5k", "3k"].map((b) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								type: "button",
								onClick: () => patch({ payloadBudget: b }),
								className: cn("h-9 rounded-md px-3 text-xs font-semibold", composer.payloadBudget === b ? "bg-card text-foreground shadow-[var(--shadow-border)]" : "text-muted-foreground"),
								children: b
							}, b))
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ToggleRow, {
						label: "Max mode",
						hint: "chirp-hawk spends more compute. Style and audio sliders lock to 1.0. Max-mode tags go in the style field.",
						checked: composer.maxMode,
						onChange: (maxMode) => patch({ maxMode })
					})
				]
			})
		]
	});
}
function Field({ label, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-2",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: label }), children]
	});
}
function ToggleRow({ label, hint, checked, onChange }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-start justify-between gap-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "text-sm font-medium",
			children: label
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "mt-0.5 text-xs text-muted-foreground",
			children: hint
		})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch, {
			checked,
			onCheckedChange: onChange,
			"aria-label": label
		})]
	});
}
var ScrollArea = import_react.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Root, {
	ref,
	className: cn("relative overflow-hidden", className),
	...props,
	children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Viewport, {
			className: "h-full w-full rounded-[inherit]",
			children
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollBar, {}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Corner, {})
	]
}));
ScrollArea.displayName = Root.displayName;
var ScrollBar = import_react.forwardRef(({ className, orientation = "vertical", ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollAreaScrollbar, {
	ref,
	orientation,
	className: cn("flex touch-none select-none transition-colors", orientation === "vertical" && "h-full w-2.5 border-l border-l-transparent p-px", orientation === "horizontal" && "h-2.5 flex-col border-t border-t-transparent p-px", className),
	...props,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollAreaThumb, { className: "relative flex-1 rounded-full bg-border" })
}));
ScrollBar.displayName = ScrollAreaScrollbar.displayName;
function GuidePanel() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollArea, {
		className: "h-full",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "space-y-8 px-5 py-5 pb-16",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "max-w-prose text-sm leading-relaxed text-muted-foreground",
					children: "Lyrical structure is the primary control surface in Suno. Style is the vehicle. Metatags are ramps. The lyric is the road."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Section, {
					title: "Feet",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "divide-y divide-border",
						children: FEET.map((f) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-baseline justify-between gap-3 py-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm font-medium",
								children: f.name
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: f.use
							})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "shrink-0 font-mono text-xs text-muted-foreground",
								children: f.pattern
							})]
						}, f.name))
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Section, {
					title: "Meterlines",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm text-muted-foreground",
						children: METERLINES.map((m) => `${m.name} (${m.feet})`).join(" · ")
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Section, {
					title: "Italian tempo",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "divide-y divide-border",
						children: TEMPO_MARKINGS.map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-baseline justify-between gap-3 py-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm",
								children: t.name
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "font-mono text-xs text-muted-foreground",
								children: [
									t.bpm,
									" · ",
									t.feel
								]
							})]
						}, t.name))
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Section, {
					title: "Rhyme schemas",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "space-y-2",
						children: RHYME_SCHEMAS.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "text-sm",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-mono text-xs text-muted-foreground",
									children: r.id
								}),
								" ",
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "text-muted-foreground",
									children: r.note
								})
							]
						}, r.id))
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Section, {
					title: "Punctuation",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "space-y-2",
						children: PUNCTUATION_NOTES.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "text-sm",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "font-medium",
								children: p.mark
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
								className: "text-muted-foreground",
								children: [" — ", p.effect]
							})]
						}, p.mark))
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Section, {
					title: "By 2s",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm leading-relaxed text-muted-foreground",
						children: "6–8 line verses, 2-line pre-chorus, 4–6 line chorus, 8–12 line bridge. Odd-line sections are high-variance. Sandwich focus tags around structure tags. Instructional tags at the start or end of a section. Return home after breaks."
					})
				})
			]
		})
	});
}
function Section({ title, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
		className: "font-display text-xl tracking-tight",
		children: title
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "mt-3",
		children
	})] });
}
function LibraryPanel({ onOpen }) {
	const library = useStudio((s) => s.library);
	const load = useStudio((s) => s.load);
	const remove = useStudio((s) => s.remove);
	if (library.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "px-5 py-10 text-sm text-muted-foreground",
		children: "Saved sheets live here. Generate, then hit Save."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollArea, {
		className: "h-full",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
			className: "space-y-1 px-3 py-3 pb-16",
			children: library.map((g) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
				className: "flex items-stretch gap-1",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
					type: "button",
					className: "min-w-0 flex-1 rounded-lg px-3 py-3 text-left hover:bg-muted",
					onClick: () => {
						load(g.id);
						onOpen?.();
					},
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "truncate text-sm font-medium",
						children: g.title
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "mt-0.5 truncate font-mono text-[11px] text-muted-foreground",
						children: [
							new Date(g.createdAt).toLocaleDateString(),
							" · ",
							g.bpm,
							" BPM · ",
							g.rhymeSchema
						]
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					type: "button",
					variant: "ghost",
					size: "icon-sm",
					className: "mt-1",
					"aria-label": `Delete ${g.title}`,
					onClick: () => remove(g.id),
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "size-4" })
				})]
			}, g.id))
		})
	});
}
function CopyBlock({ label, value, mono = true, filename, className }) {
	const [copied, setCopied] = (0, import_react.useState)(false);
	async function onCopy() {
		try {
			await navigator.clipboard.writeText(value);
			setCopied(true);
			toast("Copied", { description: label });
			window.setTimeout(() => setCopied(false), 1400);
		} catch {
			toast("Could not copy");
		}
	}
	function onDownload() {
		if (!filename) return;
		downloadBlob(new Blob([value], { type: "text/plain;charset=utf-8" }), filename);
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: cn("paper rounded-xl p-4", className),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mb-2 flex items-center justify-between gap-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "kicker",
				children: label
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex gap-1",
				children: [filename ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					type: "button",
					variant: "ghost",
					size: "sm",
					className: "h-9 px-2.5",
					onClick: onDownload,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Download, { className: "size-3.5" }), "Save"]
				}) : null, /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					type: "button",
					variant: "ghost",
					size: "sm",
					className: "h-9 px-2.5",
					onClick: onCopy,
					children: [copied ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "size-3.5" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Copy, { className: "size-3.5" }), copied ? "Copied" : "Copy"]
				})]
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
			className: cn("max-h-80 overflow-auto whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground", mono ? "font-mono" : "font-sans"),
			children: value
		})]
	});
}
function Skeleton({ className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn("animate-pulse rounded-md bg-muted", className),
		...props
	});
}
var Tabs = Root2;
var TabsList = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(List, {
	ref,
	className: cn("inline-flex h-11 items-center gap-1 rounded-lg bg-muted p-1", className),
	...props
}));
TabsList.displayName = List.displayName;
var TabsTrigger = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trigger, {
	ref,
	className: cn("inline-flex h-9 items-center justify-center rounded-md px-3 text-sm font-semibold text-muted-foreground transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-[var(--shadow-border)]", className),
	...props
}));
TabsTrigger.displayName = Trigger.displayName;
var TabsContent = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Content, {
	ref,
	className: cn("mt-0 outline-none focus-visible:ring-2 focus-visible:ring-ring/40", className),
	...props
}));
TabsContent.displayName = Content.displayName;
var ITERATIONS = [
	{
		id: "smooth",
		label: "Smooth meter",
		hint: "Smooth meterlines where enunciation would glitch; keep meaning and hook."
	},
	{
		id: "hook",
		label: "Tighter hook",
		hint: "Strengthen the chorus hook; make the title land on a stressed downbeat."
	},
	{
		id: "grit",
		label: "More grit",
		hint: "Increase masculine stress, spondees, and vocal aggression without changing the story."
	},
	{
		id: "air",
		label: "More air",
		hint: "Soften to pyrrhic/feminine flow, more blank lines, less spat delivery."
	},
	{
		id: "rhyme",
		label: "Rhyme pass",
		hint: "Upgrade rhyme schema; add internal rhyme and avoid AABB unless necessary."
	}
];
function OutputDesk({ busy, jobLabel, elapsedMs, iterateHint, onIterate }) {
	const composer = useStudio((s) => s.composer);
	const current = useStudio((s) => s.current);
	const saveCurrent = useStudio((s) => s.saveCurrent);
	const live = buildLiveStyle(composer);
	const guess = sliderGuess(composer);
	if (busy && !current) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		"aria-busy": "true",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-display text-2xl italic text-foreground",
				children: jobLabel || "Scanning the line…"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-sm tabular-nums text-ink",
				children: formatElapsed(elapsedMs ?? 0)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressRail, { indeterminate: true }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-28 w-full rounded-xl" }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64 w-full rounded-xl" }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-16 w-2/3 rounded-xl" })
		]
	});
	if (!current) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-6",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "kicker",
					children: "Live style draft"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h2", {
					className: "mt-2 font-display text-3xl leading-tight tracking-tight",
					children: ["The road is the lyric.", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "italic text-ink",
						children: " Style is the vehicle."
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-3 max-w-prose text-sm text-muted-foreground",
					children: "Write the story, pick hit DNA, then generate a paste-ready Custom Mode sheet — metatags sandwiched, meters staggered, sliders guessed."
				})
			] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
				label: "Style (updates as you write)",
				value: live
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SliderRow, { sliders: guess })
		]
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(GeneratedSheet, {
		current,
		busy,
		jobLabel,
		elapsedMs,
		iterateHint,
		live,
		onIterate,
		onSave: () => {
			saveCurrent();
			toast("Saved to library", { description: current.title });
		}
	});
}
function GeneratedSheet({ current, busy, jobLabel, elapsedMs, iterateHint, live, onIterate, onSave }) {
	const styleChars = current.stylePrompt.length;
	const lyricChars = current.lyrics.length;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-5",
		"aria-busy": busy,
		children: [
			busy ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "paper space-y-2 rounded-xl p-4",
				role: "status",
				"aria-live": "polite",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-baseline justify-between gap-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm font-medium",
						children: jobLabel || "Working the sheet…"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-xs tabular-nums text-ink",
						children: formatElapsed(elapsedMs ?? 0)
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressRail, { indeterminate: true })]
			}) : null,
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex flex-wrap items-start justify-between gap-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "kicker",
						children: "Sheet"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
						className: "mt-1 font-display text-3xl leading-tight tracking-tight",
						children: current.title
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "mt-1 font-mono text-xs tabular-nums text-muted-foreground",
						children: [
							current.engine === "cloud" ? "cloud" : current.engine === "hybrid" ? "hybrid" : "scansion-lm",
							current.guideScore ? ` · guide ${current.guideScore.passed}/${current.guideScore.total}` : "",
							" · ",
							current.sunoPackage?.json5k.mv ?? "chirp-hawk",
							current.sunoPackage?.json5k.max_mode ? " · max mode" : "",
							" · ",
							current.tempoMarking,
							" · ",
							current.bpm,
							" BPM · ",
							current.timeSignature,
							" · style ",
							current.sunoPackage?.counts.style5k ?? styleChars,
							"/",
							current.composer.payloadBudget === "3k" ? 200 : 1e3,
							" · lyrics ",
							current.sunoPackage?.counts.lyrics5k ?? lyricChars,
							"/",
							current.composer.payloadBudget === "3k" ? 3e3 : 5e3
						]
					})
				] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					type: "button",
					variant: "outline",
					size: "sm",
					onClick: onSave,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Bookmark, { className: "size-3.5" }), "Save"]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
				defaultValue: "paste",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, {
						className: "w-full justify-start overflow-x-auto",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
								value: "paste",
								children: "Paste"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
								value: "json",
								children: "JSON"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
								value: "package",
								children: "Package"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
								value: "meter",
								children: "Meter"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
								value: "notes",
								children: "Notes"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
								value: "draft",
								children: "Live draft"
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
						value: "paste",
						className: "mt-4 space-y-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
								label: "Style of music",
								value: current.stylePrompt,
								filename: "style.txt"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
								label: "Lyrics + metatags",
								value: current.lyrics,
								filename: "lyrics.txt"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SliderRow, { sliders: current.sliders })
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
						value: "json",
						className: "mt-4 space-y-3",
						children: current.sunoPackage ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(JsonPayloads, {
							pkg: current.sunoPackage,
							title: current.title
						}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm text-muted-foreground",
							children: "Generate to mint v6 hawk JSON payloads (5k and 3k)."
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
						value: "package",
						className: "mt-4",
						children: current.sunoPackage ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PackageBoard, {
							pkg: current.sunoPackage,
							title: current.title
						}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm text-muted-foreground",
							children: "Cover, tags, description, and downloadable Custom Mode bundle appear after Generate."
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
						value: "meter",
						className: "mt-4 space-y-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "text-sm text-muted-foreground",
							children: [
								"Rhyme ",
								current.rhymeSchema,
								". ",
								current.vocalBrief
							]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "space-y-2",
							children: current.meterMap.map((row) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "paper rounded-lg px-3 py-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "kicker",
									children: row.section
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "mt-1 font-mono text-xs leading-relaxed text-foreground",
									children: row.lines.join(" · ")
								})]
							}, row.section))
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
						value: "notes",
						className: "mt-4 space-y-4",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "max-w-prose text-sm leading-relaxed text-foreground",
								children: current.whyItWorks
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
								className: "space-y-2",
								children: current.sunoNotes.map((n) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", {
									className: "barline pl-3 text-sm text-muted-foreground",
									children: n
								}, n))
							}),
							current.personaClip ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "text-sm text-muted-foreground",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "text-foreground",
									children: "Persona: "
								}), current.personaClip]
							}) : null
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
						value: "draft",
						className: "mt-4",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
							label: "Form-derived style (not the generated one)",
							value: live
						})
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "kicker mb-2",
				children: "Iterate"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "flex flex-wrap gap-2",
				children: ITERATIONS.map((it) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					type: "button",
					variant: "outline",
					size: "sm",
					disabled: busy,
					"aria-busy": busy && iterateHint === it.hint,
					onClick: () => onIterate(it.hint),
					children: [busy && iterateHint === it.hint ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "size-3.5 animate-spin" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RefreshCw, { className: "size-3.5" }), busy && iterateHint === it.hint ? formatElapsed(elapsedMs ?? 0) : it.label]
				}, it.id))
			})] })
		]
	});
}
function SliderRow({ sliders }) {
	const cells = [
		{
			k: "Weirdness",
			v: sliders.weirdness
		},
		{
			k: "Style",
			v: sliders.styleInfluence
		},
		{
			k: "Audio",
			v: sliders.audioInfluence
		}
	];
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "grid grid-cols-3 gap-2",
		children: cells.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "paper rounded-lg px-3 py-3 text-center",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "kicker",
				children: c.k
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-1 font-mono text-lg tabular-nums",
				children: c.v
			})]
		}, c.k))
	});
}
function JsonPayloads({ pkg, title }) {
	const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "scansion";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-muted-foreground",
				children: "Both payloads are chirp-hawk Custom Mode JSON. 5k uses the v6 lyric cap (5000) and 1000-char style. 3k is the compact paste (3000 / 200). Max mode is on; style and audio weights are 1.0; Variety is Off so tags stay verbatim."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
				label: `5k JSON · style ${pkg.counts.style5k}/1000 · lyrics ${pkg.counts.lyrics5k}/5000`,
				value: JSON.stringify(pkg.json5k, null, 2),
				filename: `${slug}-suno-v6-hawk-5k.json`
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
				label: `3k JSON · style ${pkg.counts.style3k}/200 · lyrics ${pkg.counts.lyrics3k}/3000`,
				value: JSON.stringify(pkg.json3k, null, 2),
				filename: `${slug}-suno-v6-hawk-3k.json`
			})
		]
	});
}
function PackageBoard({ pkg, title }) {
	const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "scansion";
	const [zipping, setZipping] = (0, import_react.useState)(false);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex flex-wrap items-center justify-between gap-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm text-muted-foreground",
					children: "Full Custom Mode bundle: cover, tags, description, both JSON payloads, lyrics, style."
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					type: "button",
					size: "sm",
					disabled: zipping,
					"aria-busy": zipping,
					onClick: () => {
						setZipping(true);
						window.setTimeout(() => {
							downloadBlob(packageZip(pkg, title), `${slug}-suno-custom-mode.zip`);
							setZipping(false);
							toast("Package downloaded", { description: `${slug}-suno-custom-mode.zip` });
						}, 40);
					},
					children: [zipping ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "size-3.5 animate-spin" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Download, { className: "size-3.5" }), zipping ? "Packing…" : "Download package"]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-4 sm:grid-cols-[minmax(0,220px)_minmax(0,1fr)]",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "paper overflow-hidden rounded-xl",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "aspect-square w-full bg-muted",
						dangerouslySetInnerHTML: { __html: pkg.coverSvg.replace(/^<\?xml[^>]*>\s*/, "") }
					})
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex flex-wrap gap-1.5",
						children: pkg.tagList.slice(0, 16).map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground",
							children: t
						}, t))
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
						label: "Cover prompt",
						value: pkg.coverPrompt,
						filename: `${slug}-cover-prompt.txt`
					})]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
				label: "Description / simple-mode prompt",
				value: pkg.description,
				filename: `${slug}-description.txt`
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyBlock, {
				label: "Negative tags",
				value: pkg.negatives
			})
		]
	});
}
var Sheet = Dialog;
var SheetPortal = DialogPortal;
var SheetOverlay = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogOverlay, {
	className: cn("fixed inset-0 z-50 bg-foreground/30 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0", className),
	...props,
	ref
}));
SheetOverlay.displayName = DialogOverlay.displayName;
var SheetContent = import_react.forwardRef(({ side = "right", className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SheetPortal, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SheetOverlay, {}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
	ref,
	className: cn("fixed z-50 flex flex-col bg-card shadow-[var(--shadow-soft)] outline-none data-[state=open]:animate-in data-[state=closed]:animate-out", side === "right" && "inset-y-0 right-0 h-full w-full max-w-lg data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right", side === "left" && "inset-y-0 left-0 h-full w-full max-w-lg data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left", side === "bottom" && "inset-x-0 bottom-0 max-h-[88dvh] rounded-t-xl data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom", className),
	...props,
	children: [children, /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogClose, {
		className: "absolute right-3 top-3 inline-flex size-11 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "size-4" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "sr-only",
			children: "Close"
		})]
	})]
})] }));
SheetContent.displayName = DialogContent.displayName;
function SheetHeader({ className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn("border-b px-5 py-4 pr-14", className),
		...props
	});
}
function SheetTitle({ className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, {
		className: cn("font-display text-xl font-medium tracking-tight", className),
		...props
	});
}
function SheetDescription({ className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogDescription, {
		className: cn("mt-1 text-sm text-muted-foreground", className),
		...props
	});
}
var generateSong = createServerFn({ method: "POST" }).validator((input) => input).handler(createSsrRpc("c9b571f879f4bac6042054c75b7017ec827d271f7232d4705d466ee8f24bc1a4"));
function BrandMark() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
		className: "grid size-10 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground shadow-[var(--shadow-border)]",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-display text-2xl italic leading-none",
			children: "S"
		})
	});
}
function Studio() {
	const composer = useStudio((s) => s.composer);
	const current = useStudio((s) => s.current);
	const patch = useStudio((s) => s.patch);
	const setCurrent = useStudio((s) => s.setCurrent);
	const [job, setJob] = (0, import_react.useState)(null);
	const [guideOpen, setGuideOpen] = (0, import_react.useState)(false);
	const [libraryOpen, setLibraryOpen] = (0, import_react.useState)(false);
	const [tab, setTab] = (0, import_react.useState)("write");
	const elapsed = useElapsed(Boolean(job), job?.startedAt);
	const busy = Boolean(job);
	const phase = job ? generatePhase(elapsed, job.mode) : "";
	(0, import_react.useEffect)(() => {
		useStudio.persist.rehydrate();
	}, []);
	async function run(mode, iterateHint) {
		if (job) return;
		const startedAt = Date.now();
		setJob({
			mode,
			hint: iterateHint,
			startedAt
		});
		try {
			const result = await generateSong({ data: {
				composer,
				mode,
				iterateHint,
				previousLyrics: current?.lyrics
			} });
			const took = formatElapsed(Date.now() - startedAt);
			if (!result.ok) {
				toast("Could not generate", { description: `${result.error} · ${took}` });
				return;
			}
			const generation = {
				...result.generation,
				id: crypto.randomUUID(),
				createdAt: Date.now(),
				composer
			};
			setCurrent(generation);
			setTab("sheet");
			const guide = generation.guideScore ? `guide ${generation.guideScore.passed}/${generation.guideScore.total}` : "sheet ready";
			toast("Sheet ready", { description: `${took} · ${guide} · ${generation.lyrics.length}c lyrics · ${generation.stylePrompt.length}c style` });
		} catch (err) {
			toast("Could not generate", { description: `${err instanceof Error ? err.message : "Unknown error"} · ${formatElapsed(Date.now() - startedAt)}` });
		} finally {
			setJob(null);
		}
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "min-h-dvh text-foreground",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
				className: "sticky top-0 z-30 border-b bg-card/85 backdrop-blur-md",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex min-w-0 flex-1 items-center gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BrandMark, {}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "min-w-0",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "font-display text-2xl leading-none tracking-tight",
									children: "Scansion"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "mt-1 hidden text-sm text-muted-foreground sm:block",
									children: "Suno lyric architect · our own weights · hit DNA"
								})]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							value: composer.engine ?? "auto",
							onValueChange: (v) => patch({ engine: v }),
							disabled: busy,
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
								className: "hidden h-10 w-[7.5rem] sm:flex",
								"aria-label": "Engine",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {})
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "auto",
									children: "Auto"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "local",
									children: "Foundry"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
									value: "cloud",
									children: "Cloud"
								})
							] })]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "button",
							variant: "ghost",
							size: "sm",
							asChild: true,
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Link, {
								to: "/foundry",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FlaskConical, { className: "size-4" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "hidden sm:inline",
									children: "Foundry"
								})]
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							type: "button",
							variant: "ghost",
							size: "sm",
							onClick: () => setLibraryOpen(true),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Library, { className: "size-4" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "hidden sm:inline",
								children: "Library"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							type: "button",
							variant: "ghost",
							size: "sm",
							onClick: () => setGuideOpen(true),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BookOpen, { className: "size-4" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "hidden sm:inline",
								children: "Guide"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BusyButton, {
							type: "button",
							size: "sm",
							className: "sm:h-11 sm:px-4",
							busy,
							idle: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScanLine, { className: "size-4" }), "Generate"] }),
							pending: job?.mode === "iterate" ? `Iterate · ${formatElapsed(elapsed)}` : `Writing · ${formatElapsed(elapsed)}`,
							onClick: () => void run("generate")
						})
					]
				}), job ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(JobPulse, {
					title: phase,
					detail: job.mode === "iterate" ? "Iterate pass" : `${composer.engine ?? "auto"} · ${composer.payloadBudget} · ${composer.sunoVersion}`,
					elapsedMs: elapsed,
					stats: [
						composer.engine ?? "auto",
						composer.maxMode ? "max mode" : "standard",
						composer.payloadBudget
					]
				}) : null]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "mx-auto grid max-w-7xl gap-0 lg:grid-cols-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "hidden border-r lg:block",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "staff-ruled px-6 py-8",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Composer, {})
					})
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "hidden px-6 py-8 lg:block",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(OutputDesk, {
						busy,
						jobLabel: phase,
						elapsedMs: elapsed,
						iterateHint: job?.hint,
						onIterate: (hint) => void run("iterate", hint)
					})
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "lg:hidden",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
					value: tab,
					onValueChange: setTab,
					className: "px-4 pt-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, {
							className: "w-full",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
								value: "write",
								className: "flex-1",
								children: "Write"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsTrigger, {
								value: "sheet",
								className: "flex-1",
								children: ["Sheet", busy ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "ml-1 inline-block size-1.5 animate-pulse rounded-full bg-primary" }) : null]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
							value: "write",
							className: "mt-4 pb-10",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Composer, {})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
							value: "sheet",
							className: "mt-4 pb-10",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(OutputDesk, {
								busy,
								jobLabel: phase,
								elapsedMs: elapsed,
								iterateHint: job?.hint,
								onIterate: (hint) => void run("iterate", hint)
							})
						})
					]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Sheet, {
				open: guideOpen,
				onOpenChange: setGuideOpen,
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SheetContent, {
					side: "right",
					className: "w-full",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SheetHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SheetTitle, { children: "The code" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SheetDescription, { children: "Feet, tempo, rhyme, punctuation — the levers Suno actually hears." })] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(GuidePanel, {})]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Sheet, {
				open: libraryOpen,
				onOpenChange: setLibraryOpen,
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SheetContent, {
					side: "right",
					className: "w-full",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SheetHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SheetTitle, { children: "Library" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SheetDescription, { children: "Sheets saved on this device." })] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LibraryPanel, { onOpen: () => {
						setLibraryOpen(false);
						setTab("sheet");
					} })]
				})
			})
		]
	});
}
function Home() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Studio, {});
}
//#endregion
export { Home as component };
