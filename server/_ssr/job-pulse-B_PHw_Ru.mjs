import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { n as Slot, s as require_jsx_runtime } from "../_libs/@radix-ui/react-collection+[...].mjs";
import { c as LoaderCircle } from "../_libs/lucide-react.mjs";
import { t as cva } from "../_libs/class-variance-authority+clsx.mjs";
import { n as cn } from "./router-fI3E7ogk.mjs";
import { t as Root } from "../_libs/radix-ui__react-label.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/job-pulse-B_PHw_Ru.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var badgeVariants = cva("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide", {
	variants: { variant: {
		default: "bg-secondary text-secondary-foreground",
		outline: "shadow-[var(--shadow-border)] text-muted-foreground bg-card",
		solid: "bg-primary text-primary-foreground"
	} },
	defaultVariants: { variant: "default" }
});
function Badge({ className, variant, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn(badgeVariants({ variant }), className),
		...props
	});
}
var buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-[color,background-color,box-shadow,transform,opacity] duration-150 ease-out outline-none focus-visible:ring-2 focus-visible:ring-ring/70 disabled:pointer-events-none disabled:opacity-40 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 active:not-disabled:scale-[0.96]", {
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground hover:bg-primary/90",
			secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-[var(--shadow-border)]",
			ghost: "hover:bg-accent hover:text-accent-foreground",
			outline: "bg-transparent shadow-[var(--shadow-border)] hover:shadow-[var(--shadow-border-hover)] hover:bg-accent",
			destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90"
		},
		size: {
			default: "h-11 px-4",
			sm: "h-9 px-3 text-xs",
			lg: "h-12 px-5",
			icon: "size-11",
			"icon-sm": "size-9"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
var Button = import_react.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(asChild ? Slot : "button", {
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		ref,
		...props
	});
});
Button.displayName = "Button";
var Input = import_react.forwardRef(({ className, type, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
		type,
		className: cn("flex h-11 w-full rounded-md bg-card px-3 text-sm text-foreground shadow-[var(--shadow-border)] outline-none transition-[box-shadow] duration-150 placeholder:text-muted-foreground/80 focus-visible:ring-2 focus-visible:ring-ring/70 disabled:cursor-not-allowed disabled:opacity-50", className),
		ref,
		...props
	});
});
Input.displayName = "Input";
var Label = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Root, {
	ref,
	className: cn("kicker", className),
	...props
}));
Label.displayName = Root.displayName;
var Textarea = import_react.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("textarea", {
		className: cn("flex min-h-28 w-full rounded-lg bg-card px-3 py-3 text-sm text-foreground shadow-[var(--shadow-border)] outline-none transition-[box-shadow] duration-150 placeholder:text-muted-foreground/80 focus-visible:ring-2 focus-visible:ring-ring/70 disabled:cursor-not-allowed disabled:opacity-50", className),
		ref,
		...props
	});
});
Textarea.displayName = "Textarea";
function useElapsed(active, startedAt) {
	const [ms, setMs] = (0, import_react.useState)(0);
	(0, import_react.useEffect)(() => {
		if (!active) {
			setMs(0);
			return;
		}
		const t0 = startedAt ?? Date.now();
		const tick = () => setMs(Date.now() - t0);
		tick();
		const id = window.setInterval(tick, 200);
		return () => window.clearInterval(id);
	}, [active, startedAt]);
	return ms;
}
function formatElapsed(ms) {
	const s = Math.max(0, Math.floor(ms / 1e3));
	if (s < 60) return `${s}s`;
	return `${Math.floor(s / 60)}m ${(s % 60).toString().padStart(2, "0")}s`;
}
function generatePhase(ms, mode) {
	const s = ms / 1e3;
	if (mode === "iterate") {
		if (s < 3) return "Reopening the sheet";
		if (s < 10) return "Rewriting the pass";
		if (s < 20) return "Re-wrapping hawk JSON";
		return "Still iterating — the engine is on the CPU";
	}
	if (s < 2) return "Waking Scansion-LM";
	if (s < 8) return "Pausing trainer · loading checkpoint";
	if (s < 20) return "Writing verses from the weights";
	if (s < 40) return "Filling chorus and bridge";
	if (s < 70) return "Still decoding — checkpoint is working";
	return "Holding for the model · no fallback";
}
function foundryPhase(kind, ms) {
	const s = ms / 1e3;
	if (kind === "pull") {
		if (s < 3) return "Opening Suno homepage";
		if (s < 9) return "Walking curated playlists";
		if (s < 16) return "Ranking plays and display tags";
		return "Still reading Suno";
	}
	if (kind === "bulk") {
		if (s < 4) return "Ingesting public prompts";
		return "Handing extracts to the trainer";
	}
	if (kind === "train") return "Fine-tuning distilgpt2";
	if (kind === "eval") {
		if (s < 20) return "Writing eval sheets";
		if (s < 80) return "Scoring against the guide";
		return "Still evaluating — three full inferences";
	}
	if (kind === "export") return "Writing safetensors and tokenizer";
	if (kind === "extract") return "Counting feet and rhyme";
	if (kind === "ingest") return "Saving extract for the next train";
	return "Working";
}
function ProgressRail({ value, indeterminate, className }) {
	const pct = Math.max(0, Math.min(100, (value ?? 0) * 100));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn("h-1.5 overflow-hidden rounded-full bg-muted", className),
		role: "progressbar",
		"aria-valuemin": 0,
		"aria-valuemax": 100,
		"aria-valuenow": indeterminate ? void 0 : Math.round(pct),
		"aria-busy": indeterminate || pct < 100,
		children: indeterminate ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "job-shimmer h-full w-1/3 rounded-full bg-primary" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "h-full rounded-full bg-primary transition-[width] duration-300 ease-out",
			style: { width: `${pct}%` }
		})
	});
}
function JobPulse({ title, detail, elapsedMs, progress, stats, className }) {
	const indeterminate = progress == null;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn("border-b bg-accent/70 px-4 py-2.5 sm:px-6", className),
		role: "status",
		"aria-live": "polite",
		"aria-busy": "true",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto flex max-w-7xl items-center gap-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
				className: "relative grid size-2.5 shrink-0 place-items-center",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "absolute size-2.5 animate-ping rounded-full bg-primary/50" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "size-2 rounded-full bg-primary" })]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "min-w-0 flex-1",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex flex-wrap items-baseline gap-x-3 gap-y-0.5",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm font-medium text-foreground",
								children: title
							}),
							detail ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "truncate text-xs text-muted-foreground",
								children: detail
							}) : null,
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "ml-auto font-mono text-xs tabular-nums text-ink",
								children: formatElapsed(elapsedMs)
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressRail, {
						className: "mt-1.5",
						value: progress,
						indeterminate
					}),
					stats?.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-1 font-mono text-[11px] tabular-nums text-muted-foreground",
						children: stats.join(" · ")
					}) : null
				]
			})]
		})
	});
}
function BusyButton({ busy, idle, pending, children, className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
		className,
		...props,
		disabled: busy || props.disabled,
		"aria-busy": busy,
		children: [busy ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "size-4 animate-spin" }) : null, busy ? pending : idle]
	});
}
//#endregion
export { JobPulse as a, Textarea as c, generatePhase as d, useElapsed as f, Input as i, formatElapsed as l, BusyButton as n, Label as o, Button as r, ProgressRail as s, Badge as t, foundryPhase as u };
