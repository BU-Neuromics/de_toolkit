"""Every report view text field renders as text, not markup (#65, DETK-0022).

The report page builds each module's card from a view descriptor. A filter
command, DE term names, annotation and gather notes, an unknown module's name
and a builder's error text all carry user strings; the page must show them as
written and never parse them as HTML. Only the static SVG chart is markup.

The DOM tests render a real report and run the page's own script in jsdom
(``render_dom.js``). They need node and jsdom (``npm install jsdom``, then
point ``NODE_PATH`` at its ``node_modules``) and are skipped without them; the
template checks below run everywhere. The harness renders the Vega charts
too (it stubs a canvas and ``structuredClone``), hovers every mark that has a
tooltip (through the view's own tooltip handler), clicks every action in their
menus, waits for every export and fails on any page error.
"""

import json
import os
import re
import shutil
import subprocess

import pytest

from de_toolkit import report_specs
from de_toolkit.report import DetkReport

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(HERE, "render_dom.js")
TEMPLATE = os.path.join(HERE, os.pardir, os.pardir, "de_toolkit", "templates", "report.html")

# breaks out of an attribute, opens elements with handlers, and carries an
# entity that must stay literal
EVIL = "\"'><img src=x onerror=alert(1)><script>alert(2)</script>&amp;<b>x</b>"
UNKNOWN = "x" + EVIL

# the elements the card builder itself makes (charts' contents excluded)
BUILT = {"a", "button", "div", "h2", "p", "pre", "section", "table", "tbody", "td", "th", "tr"}


def _jsdom_available():
    node = shutil.which("node")
    if not node:
        return False
    p = subprocess.run(
        [node, "-e", "require.resolve('jsdom')"], capture_output=True, text=True, cwd=HERE
    )
    return p.returncode == 0


needs_jsdom = pytest.mark.skipif(
    not _jsdom_available(), reason="node with jsdom is required (set NODE_PATH)"
)


def _mod(name, properties, params=None):
    return {
        "name": name,
        "params": params or {},
        "properties": properties,
        "detk_version": "0.0.0",
        "in_file_path": "counts.csv",
    }


def _de_terms(term, n, shown=None):
    points = [
        {"feature": f"g{i}", "effect": (i % 7) - 3.0, "nlp": (i % 11) / 2.0, "sig": "ns"}
        for i in range(n)
    ]
    return {
        "de": {
            "terms": [
                {
                    "term": term,
                    "total": 60000 if shown is not None else n,
                    "shown": shown if shown is not None else n,
                    "num_sig": 0,
                    "sig_threshold": 0.05,
                    "points": points,
                }
            ]
        }
    }


def _write_report(tmp_path, mods):
    rep = DetkReport(str(tmp_path / "rep"), crate_dir=str(tmp_path))
    for i, m in enumerate(mods):
        with open(os.path.join(rep.json_dir, f"m{i}.json"), "w") as f:
            json.dump(m, f)
    rep.write()
    return rep.report_path


# the only actions a chart's menu may offer: both download a file
EXPORTS = ["Save as SVG", "Save as PNG"]
ACTIONS = {"export": True, "source": False, "compiled": False, "editor": False}


def _render(path):
    p = subprocess.run(
        ["node", HARNESS, path], capture_output=True, text=True, cwd=HERE, timeout=120
    )
    # the harness exits non-zero on any page error, a failed chart included
    assert p.returncode == 0, p.stderr[-2000:]
    page = json.loads(p.stdout)
    assert page["errors"] == []
    return page


def _no_markup(page):
    assert page["injected"] == 0
    assert page["handlers"] == []
    assert page["alerts"] == []
    # the three vendored libraries, the two payloads and the app
    assert page["scripts"] == 6
    assert set(page["tags"]) <= BUILT, set(page["tags"]) - BUILT
    # no chart asks for View Source, View Compiled Vega or Open in Vega
    # Editor, and clicking every action that is offered opens no window
    assert all(e["actions"] == ACTIONS for e in page["embeds"])
    # every chart uses the page's own tooltip, which writes text only
    assert all(e["tooltip"] == "function" for e in page["embeds"])
    for t in page["tooltips"]:
        assert t["shown"], t
        assert t["injected"] == t["handlers"] == 0, t
        assert set(t["tags"]) <= {"div", "span"}, t
    assert all(c["actions"] in ([], EXPORTS) for c in page["cards"])
    assert page["opened"] == [] and page["written"] == []
    for x in page["exports"]:
        assert x["svg"] is None or x["svg"]["injected"] == x["svg"]["handlers"] == 0
    # ids are unique across the whole page, chart containers included
    assert len(set(page["ids"])) == len(page["ids"])
    for x in page["exports"]:
        assert x["download"] in ("visualization.svg", "visualization.png"), x


def _card(page, module):
    (card,) = [c for c in page["cards"] if c["dataMod"] == module]
    return card


def _hostile_mods():
    return [
        _mod(
            "filtercounts", {"num_kept": 5, "num_filtered": 1}, {"command": "mean(all) > 1 " + EVIL}
        ),
        _mod("deseq2counts", _de_terms(EVIL, 20, shown=20)),
        _mod(
            "annotate",
            {
                "num_features": 2,
                "num_mapped": 1,
                "columns_added": [EVIL],
                "unmapped_examples": [EVIL],
            },
        ),
        _mod(
            "gather",
            {
                "format": EVIL,
                "column": EVIL,
                "num_samples": 1,
                "num_features": 3,
                "samples": [{"name": EVIL}],
            },
        ),
        _mod("pca", {}),  # its builder raises (patched below)
        _mod("basestats", {"num_rows": 1, "num_cols": 1}),  # a table (patched below)
        _mod(UNKNOWN, {}),
    ]


@pytest.fixture
def hostile_builders(monkeypatch):
    """A builder whose exception quotes user data, and a table view with user
    strings in its title, description, columns and cells."""

    def raising(mod):
        raise ValueError("bad sample " + EVIL)

    def table(mod):
        return {"type": "table", "columns": ["sample", EVIL], "rows": [[EVIL, 1.5], ["s2", None]]}

    fam, title, desc, _ = report_specs.REGISTRY["pca"]
    monkeypatch.setitem(report_specs.REGISTRY, "pca", (fam, title, desc, raising))
    fam = report_specs.REGISTRY["basestats"][0]
    monkeypatch.setitem(report_specs.REGISTRY, "basestats", (fam, "T " + EVIL, "D " + EVIL, table))


def test_template_inserts_markup_only_for_the_static_svg():
    with open(TEMPLATE, encoding="utf-8") as f:
        page = f.read()
    sites = re.findall(r"(\S+)\.(innerHTML|outerHTML)\s*=\s*([^;]+);", page)
    assert sites == [("box", "innerHTML", "v.svg")]
    assert "insertAdjacentHTML" not in page and "document.write" not in page


def test_template_offers_no_chart_source_view():
    # View Source and View Compiled Vega write the spec unescaped into a
    # same-origin window; Open in Vega Editor sends it to an outside site
    with open(TEMPLATE, encoding="utf-8") as f:
        page = f.read()
    (actions,) = re.findall(r"actions:\s*(\{[^}]*\})", page)
    assert json.loads(re.sub(r"(\w+):", r'"\1":', actions)) == ACTIONS
    # chart containers end in "_vis", which domId never produces
    assert 'vis.id = cardId + "_vis";' in page


def test_template_sets_its_own_tooltip():
    # vega-embed's default tooltip (vega-tooltip) writes innerHTML and turns
    # an "image" field into an <img>: the page passes a handler that writes
    # text (and the innerHTML check above covers that handler too)
    with open(TEMPLATE, encoding="utf-8") as f:
        page = f.read()
    assert re.findall(r"\btooltip:\s*([^,\s]+)", page) == ["showTooltip"]
    (body,) = re.findall(r"function showTooltip\(.*?\n  \}\n", page, re.S)
    assert "textContent" in body and "innerHTML" not in body and "<img" not in body


def test_builders_leave_notes_unescaped(hostile_builders):
    # escaping is the page's job now: a builder that escaped would show
    # "&lt;" to the user
    for m in _hostile_mods()[:4]:
        _, _, _, view = report_specs.view_for(m)
        assert EVIL in view["note"], m["name"]


@needs_jsdom
def test_hostile_view_text_renders_as_text(tmp_path, hostile_builders):
    page = _render(_write_report(tmp_path, _hostile_mods()))
    _no_markup(page)
    assert len(page["cards"]) == 7

    fc = _card(page, "filtercounts")
    assert fc["desc"][-1] == "filter command: mean(all) > 1 " + EVIL

    de = _card(page, "deseq2counts")
    assert any(EVIL in s and "density-preserving" in s for s in de["desc"])
    assert de["vis"] == ["deseq2counts_vis"]
    assert de["actions"] == EXPORTS  # the chart rendered

    ann = _card(page, "annotate")
    assert ann["desc"][-1] == f"columns added: {EVIL}; unmapped e.g.: {EVIL}"

    ga = _card(page, "gather")
    assert ga["desc"][-1] == f"samples: {EVIL}"
    assert ga["vals"][:2] == [EVIL, EVIL]

    err = _card(page, "pca")
    assert err["desc"][-2] == "chart error: bad sample " + EVIL

    tab = _card(page, "basestats")
    assert tab["h2"] == "T " + EVIL
    assert tab["desc"][0] == "D " + EVIL
    assert tab["ths"] == ["sample", EVIL]
    assert tab["tds"] == [EVIL, "1.500", "s2", "—"]

    # an unknown module's name is its title, its id, its data key and the
    # file name on the Show data button
    unk = _card(page, UNKNOWN)
    assert unk["h2"] == UNKNOWN
    assert unk["button"] == f"Show data ({UNKNOWN}.json)"
    assert unk["shownName"] == UNKNOWN
    assert re.fullmatch(r"[A-Za-z0-9_-]+", unk["id"])
    (link,) = [a for a in page["nav"] if a["text"] == UNKNOWN]
    assert link["href"] == "#" + unk["id"] and link["target"] == unk["id"]
    # ids stay unique and the known modules' ids are unchanged
    ids = [c["id"] for c in page["cards"]]
    assert len(set(ids)) == len(ids)
    assert {"filtercounts", "deseq2counts", "annotate", "gather", "pca", "basestats"} <= set(ids)


@needs_jsdom
def test_static_svg_still_renders_as_svg(tmp_path):
    pytest.importorskip("matplotlib")
    from de_toolkit.static_plots import MAX_INTERACTIVE_POINTS

    mods = [_mod("flgcounts", _de_terms(EVIL, MAX_INTERACTIVE_POINTS + 1))]
    page = _render(_write_report(tmp_path, mods))
    _no_markup(page)

    (card,) = page["cards"]
    svg = card["svg"]
    assert svg is not None, "no <svg> element in the static chart"
    assert svg["namespace"] == "http://www.w3.org/2000/svg"
    assert svg["elements"] > 20  # axes, ticks, labels: parsed, not shown as text
    assert svg["injected"] == 0
    # the note naming the term (as a Python repr) is text
    assert any(s.startswith("Rendered statically") and repr(EVIL) in s for s in card["desc"])


@needs_jsdom
def test_chart_actions_never_write_sample_names_as_markup(tmp_path):
    # vega-embed's View Source document.writes the spec's JSON, sample names
    # and all, unescaped into a same-origin window: the page must not offer it
    names = [EVIL, "</code></pre><img src=x onerror=alert(3)>", "s3"]
    dists = [{"name": n, "percentiles": [[0.0, 0], [0.5, 10], [1.0, 100]]} for n in names]
    page = _render(_write_report(tmp_path, [_mod("coldist", {"dists": dists})]))
    _no_markup(page)

    (card,) = page["cards"]
    assert card["vis"] == ["coldist_vis"]
    assert card["actions"] == EXPORTS
    (embed,) = page["embeds"]
    assert embed["target"] == "coldist_vis"
    # the SVG export draws the names as text
    (svg,) = [x["svg"] for x in page["exports"] if x["svg"]]
    assert svg["root"] == "svg"
    assert all(n in svg["text"] for n in names)


@needs_jsdom
def test_unknown_module_named_like_a_chart_does_not_collide(tmp_path):
    # domId keeps "-", so an unknown module "deseq2counts-vis" has that card
    # id; the chart containers end in "_vis", which domId never produces
    mods = [_mod("deseq2counts", _de_terms("t", 5)), _mod("deseq2counts-vis", {})]
    page = _render(_write_report(tmp_path, mods))
    _no_markup(page)

    de = _card(page, "deseq2counts")
    unk = _card(page, "deseq2counts-vis")
    assert unk["id"] == "deseq2counts-vis"
    assert de["vis"] == ["deseq2counts_vis"]
    assert de["actions"] == EXPORTS
    (link,) = [a for a in page["nav"] if a["target"] == "deseq2counts-vis"]
    assert link["href"] == "#deseq2counts-vis"
    assert page["ids"].count("deseq2counts-vis") == 1


def _pca(covs):
    samples = ["s1", "s2", "s3"]
    return _mod(
        "pca",
        {
            "column_names": samples,
            "column_variables": {
                "sample_names": samples,
                "columns": [{"column": c, "values": v} for c, v in covs.items()],
            },
            "components": [
                {"name": "PC1", "scores": [1.0, -2.0, 0.5], "perc_variance": 0.4},
                {"name": "PC2", "scores": [0.2, 0.1, -0.3], "perc_variance": 0.2},
            ],
        },
    )


@needs_jsdom
def test_tooltip_shows_a_normal_point_as_key_value_text(tmp_path):
    page = _render(_write_report(tmp_path, [_pca({"status": ["A", "B", "A"]})]))
    _no_markup(page)
    tips = [t for t in page["tooltips"] if t["target"] == "pca_vis"]
    assert len(tips) == 3
    assert ["sample: s1", "PC1: 1.00", "PC2: 0.20", "status: A"] in [t["rows"] for t in tips]


@needs_jsdom
def test_tooltip_writes_hostile_fields_as_text(tmp_path):
    # a covariate column named "image" became <img src="..."> in vega-tooltip,
    # and a data: URL keeps its '"', so this value added an onerror handler
    img = 'data:x"onerror="alert(document.domain)//'
    # a column name with a quote, "." or "[" breaks Vega's field path (out of
    # scope here), so the hostile name has none
    name = "<img src=x onerror=alert(7)><b>x</b>"
    covs = {"image": [img] * 3, "title": [EVIL] * 3, name: [EVIL] * 3}
    page = _render(_write_report(tmp_path, [_pca(covs)]))
    _no_markup(page)
    tips = [t for t in page["tooltips"] if t["target"] == "pca_vis"]
    assert len(tips) == 3
    for t in tips:
        assert t["rows"][3:] == [f"image: {img}", f"title: {EVIL}", f"{name}: {EVIL}"]
    assert page["alerts"] == []


# the ids the page and vega-embed give their own elements
RESERVED = [
    "main",
    "nav",
    "meta",
    "tray-toggle",
    "theme-toggle",
    "theme-icon",
    "theme-label",
    "detk-modules",
    "detk-raw",
    "detk-tooltip",
    "vg-tooltip-element",
    "vega-embed-style",
    "vega-tooltip-style",
]


@needs_jsdom
def test_module_named_like_a_page_element_gets_another_id(tmp_path):
    mods = [_pca({"status": ["A", "B", "A"]})] + [_mod(n, {}) for n in RESERVED]
    mods.append(_mod("_6d_ain", {}))  # what "main" becomes, written out
    page = _render(_write_report(tmp_path, mods))
    _no_markup(page)
    for n in RESERVED:
        card = _card(page, n)
        assert card["id"] not in RESERVED
        assert card["id"] == f"_{ord(n[0]):x}_{n[1:]}"
        assert card["shownName"] == n
        (link,) = [a for a in page["nav"] if a["text"] == n]
        assert link["href"] == "#" + card["id"]
    assert _card(page, "main")["id"] == "_6d_ain"
    assert _card(page, "_6d_ain")["id"] == "_5f_6d_5f_ain"
    # the page's own elements and the tooltip keep their ids
    for n in ["main", "nav", "meta", "theme-icon", "theme-toggle", "detk-raw", "detk-tooltip"]:
        assert page["ids"].count(n) == 1, n
    # registered modules keep their plain ids
    assert _card(page, "pca")["id"] == "pca"
