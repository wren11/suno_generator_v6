import { t as createServerFn } from "./ssr.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { t as HITS } from "./hits-DKJ_Fcz3.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/trending-D4NJZGP2.js
var FOUNDRY = "http://127.0.0.1:8099";
new Set(HITS.map((h) => h.title.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim()));
var memory = null;
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
async function learnedTagStrings(n = 10) {
	return ((await loadPersisted())?.topTags ?? []).slice(0, n).map((t) => t.tag);
}
var getTrendingLearn = createServerFn({ method: "GET" }).handler(createSsrRpc("f478ff78d7312f6d550081b556e53a2a3f466fba939408e9827bbf38b540440c"));
var pullSunoTrending = createServerFn({ method: "POST" }).handler(createSsrRpc("52d13663e92f951a7e84866dcbb607673741a9a2590dd2ef607e62e4bdc4c3d4"));
var ingestTrending = createServerFn({ method: "POST" }).handler(createSsrRpc("ba3d901cde197839234a1f944f5dd303b28e1b84eb948f8b7469f0e8c469706d"));
//#endregion
export { pullSunoTrending as i, ingestTrending as n, learnedTagStrings as r, getTrendingLearn as t };
