// Load a detk report in jsdom, let the page's own script build the cards, and
// print what it built as JSON (#65). Used by test_report_view_text.py.
//
//   node render_dom.js detk_report.html
//
// jsdom must be resolvable by node (installed nearby, or on NODE_PATH).
"use strict";

const fs = require("fs");
const { JSDOM, VirtualConsole } = require("jsdom");

const html = fs.readFileSync(process.argv[2], "utf8");
const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errors.push(String(e && e.message)));

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  pretendToBeVisual: true,
  virtualConsole: vc,
  beforeParse(w) {
    w.__alerts = [];
    w.alert = (x) => w.__alerts.push(String(x));
    w.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
    w.HTMLCanvasElement.prototype.getContext = () => null;
  },
});
const w = dom.window;
const d = w.document;

// the page builds its cards synchronously while the document is parsed
const text = (n) => (n ? n.textContent : null);
const all = (root, sel) => Array.from(root.querySelectorAll(sel));

// every element the card builder made, outside the chart containers (whose
// contents come from Vega or from the static SVG)
function builtTags(root) {
  const tags = new Set();
  for (const e of all(root, "*")) {
    if (e.closest(".chart") && !e.classList.contains("chart")) continue;
    tags.add(e.tagName.toLowerCase());
  }
  return [...tags].sort();
}

// elements carrying an event-handler attribute, anywhere in the body
const handlers = all(d.body, "*")
  .filter((e) => [...e.attributes].some((a) => /^on/i.test(a.name)))
  .map((e) => e.outerHTML.slice(0, 200));

const cards = all(d, "#main section.card").map((c) => {
  const btn = c.querySelector(".tools button");
  // the "Show data" button looks its module up by data-mod
  btn.click();
  const pre = c.querySelector("pre.data");
  let shown = null;
  try {
    shown = JSON.parse(pre.textContent);
  } catch (e) {}
  const svg = c.querySelector(".chart-static svg");
  return {
    id: c.id,
    h2: text(c.querySelector("h2")),
    desc: all(c, ":scope > p.desc").map(text),
    vals: all(c, ".kv .val").map(text),
    labs: all(c, ".kv .lab").map(text),
    ths: all(c, "table.detk th").map(text),
    tds: all(c, "table.detk td").map(text),
    button: text(btn),
    dataMod: btn.getAttribute("data-mod"),
    shownName: shown && shown.name,
    vis: all(c, ".chart:not(.chart-static)").map((e) => e.id),
    svg: svg
      ? {
          namespace: svg.namespaceURI,
          elements: svg.querySelectorAll("*").length,
          injected: all(svg, "img, script, iframe, foreignObject").length,
        }
      : null,
  };
});

const nav = all(d, "#nav a").map((a) => ({
  text: text(a),
  href: a.getAttribute("href"),
  target: a.dataset.target,
}));

process.stdout.write(
  JSON.stringify({
    cards,
    nav,
    families: all(d, "#nav .fam").map(text),
    tags: builtTags(d.getElementById("main")).concat(builtTags(d.getElementById("nav"))),
    injected: all(d.body, "img, iframe, object, embed").length,
    scripts: d.querySelectorAll("script").length,
    handlers,
    alerts: w.__alerts,
    errors,
  })
);
process.exit(0);
