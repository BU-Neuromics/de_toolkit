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
// a rejection no one handles (an action's async handler, say) is an error too
process.on("unhandledRejection", (e) => errors.push(String((e && e.message) || e)));

// every vegaEmbed call the page makes (its options), every window.open and
// every document.write into an opened window
const embeds = [];
const opened = [];
const written = [];
const blobs = [];

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  pretendToBeVisual: true,
  virtualConsole: vc,
  beforeParse(w) {
    w.__alerts = [];
    w.alert = (x) => w.__alerts.push(String(x));
    w.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
    // jsdom has no canvas: a 2D context that draws nothing, so Vega's canvas
    // renderer runs (every method a no-op, text 0 wide, properties kept)
    w.HTMLCanvasElement.prototype.getContext = function () {
      const props = {};
      const noop = () => ({ width: 0 });
      return new Proxy(props, {
        get: (t, k) => (k in t ? t[k] : noop),
        set: (t, k, v) => ((t[k] = v), true),
      });
    };
    w.HTMLCanvasElement.prototype.toDataURL = () => "data:image/png;base64,";
    // an SVG export is a Blob URL: keep the Blob to read it back
    w.URL.createObjectURL = (b) => "blob:detk/" + (blobs.push(b) - 1);
    // jsdom has no structuredClone, and vega-lite needs it to compile a spec
    w.structuredClone = (x) => JSON.parse(JSON.stringify(x));
    w.open = (url) => {
      opened.push(String(url));
      return {
        document: { write: (s) => written.push(String(s)), title: "" },
        postMessage() {},
      };
    };
    // wrap vegaEmbed when the vendored script defines it, to see the options
    // and to wait for every chart
    let embed;
    Object.defineProperty(w, "vegaEmbed", {
      configurable: true,
      get: () => embed,
      set(f) {
        embed = function (el, spec, opts) {
          const p = f.apply(this, arguments);
          embeds.push({ target: el.id, actions: (opts || {}).actions, done: p });
          return p;
        };
      },
    });
  },
});
const w = dom.window;
const d = w.document;

function readBlob(b) {
  return new Promise((resolve, reject) => {
    const r = new w.FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = () => reject(r.error);
    r.readAsText(b);
  });
}

async function main() {
  // the page builds its cards synchronously while the document is parsed; the
  // charts embed asynchronously
  for (const e of embeds) {
    try {
      await e.done;
    } catch (err) {
      errors.push("embed " + e.target + ": " + String(err && err.message));
    }
  }
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
      // the chart's "..." menu, as vega-embed rendered it
      actions: all(c, ".chart .vega-actions a").map(text),
      svg: svg
        ? {
            namespace: svg.namespaceURI,
            elements: svg.querySelectorAll("*").length,
            injected: all(svg, "img, script, iframe, foreignObject").length,
          }
        : null,
    };
  });

  // click every action in every chart menu: none may open a window
  for (const a of all(d, ".vega-actions a")) {
    a.dispatchEvent(new w.MouseEvent("mousedown", { bubbles: true }));
    a.click();
  }
  await new Promise((r) => setTimeout(r, 100));
  // an export link's href is now a Blob URL to download; an SVG export holds
  // the chart's text, which must stay text there too
  const exports = [];
  for (const a of all(d, ".vega-actions a[download]")) {
    const m = /^blob:detk\/(\d+)$/.exec(a.getAttribute("href") || "");
    if (!m) {
      exports.push({ download: a.getAttribute("download"), svg: null });
      continue;
    }
    const src = await readBlob(blobs[+m[1]]);
    const doc = new w.DOMParser().parseFromString(src, "image/svg+xml");
    exports.push({
      download: a.getAttribute("download"),
      svg: {
        root: doc.documentElement.tagName,
        text: doc.documentElement.textContent,
        injected: all(doc, "img, script, foreignObject, iframe").length,
        handlers: all(doc, "*").filter((e) => [...e.attributes].some((x) => /^on/i.test(x.name)))
          .length,
      },
    });
  }

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
      ids: all(d, "[id]").map((e) => e.id),
      embeds: embeds.map((e) => ({ target: e.target, actions: e.actions })),
      opened,
      written,
      exports,
      errors,
    })
  );
  if (errors.length) process.stderr.write(errors.join("\n"));
  process.exit(errors.length ? 1 : 0);
}

main().catch((e) => {
  process.stderr.write(String((e && e.stack) || e));
  process.exit(2);
});
