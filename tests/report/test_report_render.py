"""Tests for the Vega-Lite report rendering pipeline (Phase 2)."""

import json
import os
import re

import pytest

from de_toolkit.report_specs import clean, view_for


def mod(name, properties, params=None):
    return {
        "name": name,
        "params": params or {},
        "properties": properties,
        "detk_version": "0.0.0",
        "in_file_path": "counts.csv",
    }


# synthetic module JSON matching the real emitted shapes
FIXTURES = {
    "basestats": mod("basestats", {"num_rows": 100, "num_cols": 6}),
    "pca": mod(
        "pca",
        {
            "column_names": ["s1", "s2", "s3"],
            "column_variables": {
                "sample_names": ["s1", "s2", "s3"],
                "columns": [{"column": "status", "values": ["A", "B", "A"]}],
            },
            "components": [
                {
                    "name": "PC1",
                    "scores": [1.0, -2.0, 0.5],
                    "perc_variance": 0.4,
                    "projections": [],
                },
                {
                    "name": "PC2",
                    "scores": [0.2, 0.1, -0.3],
                    "perc_variance": 0.2,
                    "projections": [],
                },
            ],
        },
    ),
    "entropy": mod(
        "entropy",
        {"entropies": {"pct": [0, 1, 2], "pctVal": [0.5, 1.0, 1.5], "num_features": [1, 2, 3]}},
    ),
    "colzero": mod(
        "colzero", {"zeros": [{"name": "s1", "zero_frac": 0.1}, {"name": "s2", "zero_frac": 0.3}]}
    ),
    "rowzero": mod(
        "rowzero",
        {
            "zeros": [
                {"num_zeros": 0, "num_features": 50, "feature_frac": 0.5},
                {"num_zeros": 1, "num_features": 30, "feature_frac": 0.3},
            ]
        },
    ),
    "coldist": mod(
        "coldist",
        {
            "dists": [
                {
                    "name": "s1",
                    "dist": [[0, 5], [10, 2]],
                    "percentiles": [[0.0, 0.0], [0.5, 10.0], [1.0, 20.0]],
                }
            ]
        },
    ),
    "rowdist": mod(
        "rowdist",
        {
            "pct": [5, 10],
            "dists": [{"name": "g1", "dist": [3, 1], "bins": [0.0, 5.0], "extrema": {}}],
        },
    ),
}


def test_clean_nonfinite_is_valid_json():
    d = {
        "a": float("nan"),
        "b": [1.0, float("inf"), 3.0],
        "c": {"x": float("-inf")},
        "ok": 2.5,
        "s": "keep",
    }
    c = clean(d)
    assert c["a"] is None
    assert c["b"] == [1.0, None, 3.0]
    assert c["c"]["x"] is None
    assert c["ok"] == 2.5 and c["s"] == "keep"
    json.dumps(c)  # must not raise (no bare NaN/Inf)


OUTLIER_FIXTURES = {
    "entropycounts": mod(
        "entropycounts",
        {
            "num_kept": 100,
            "num_flagged": 5,
            "entropy_threshold": 0.42,
            "entropies": {"pct": list(range(100)), "pctVal": [i / 100 for i in range(100)]},
        },
        params={"threshold": 5},
    ),
    "shrinkcounts": mod(
        "shrinkcounts",
        {"num_kept": 100},
        params={"shrink_factor": 0.25, "p_max": None, "iters": 1000},
    ),
    "pmftransform": mod(
        "pmftransform",
        {"num_kept": 100},
        params={"shrink_factor": 0.25, "p_max": 0.3, "iters": 1000},
    ),
}


@pytest.mark.parametrize("name", list(OUTLIER_FIXTURES))
def test_view_for_outlier_family(name):
    family, title, desc, view = view_for(OUTLIER_FIXTURES[name])
    assert family == "outlier"
    assert title
    assert view["type"] in ("vega", "kv")


def test_entropycounts_marks_module_threshold():
    _, _, _, view = view_for(OUTLIER_FIXTURES["entropycounts"])
    spec = json.dumps(view["spec"])
    assert '"datum": 5' in spec or '"datum": 5.0' in spec  # rule at params threshold
    assert "5 flagged" in spec


def test_every_detk_module_has_a_registry_entry():
    """Every DetkModule subclass must resolve to a real family, so a new
    module can never silently fall into the 'other' bucket again (#10)."""
    import importlib
    import inspect

    from de_toolkit import report_specs
    from de_toolkit.common import DetkModule

    # modules whose `name` property differs from the lowercased class name
    name_overrides = {"countpca": "pca"}

    emitted = set()
    for modname in ("de", "norm", "transform", "filter", "stats", "outlier", "enrich"):
        pymod = importlib.import_module(f"de_toolkit.{modname}")
        for _, cls in inspect.getmembers(pymod, inspect.isclass):
            if (
                issubclass(cls, DetkModule)
                and cls is not DetkModule
                and cls.__module__ == f"de_toolkit.{modname}"
            ):
                default = cls.__name__.lower()
                emitted.add(name_overrides.get(default, default))

    known = set(report_specs.REGISTRY) | set(report_specs._FALLBACK_FAMILIES)
    missing = emitted - known
    assert not missing, f"modules that would land in the 'other' family: {sorted(missing)}"


@pytest.mark.parametrize("name", list(FIXTURES))
def test_view_for_stats_family(name):
    family, title, desc, view = view_for(FIXTURES[name])
    assert family == "stats"
    assert title
    assert view["type"] in ("vega", "kv", "table", "raw")
    if view["type"] == "vega":
        assert "$schema" in view["spec"]
        assert "data" in view["spec"] or "layer" in view["spec"]


@pytest.mark.parametrize("name", list(FIXTURES) + list(OUTLIER_FIXTURES))
def test_specs_compile(name):
    vlc = pytest.importorskip("vl_convert")
    _, _, _, view = view_for({**FIXTURES, **OUTLIER_FIXTURES}[name])
    if view["type"] != "vega":
        pytest.skip("not a vega view")
    svg = vlc.vegalite_to_svg(json.dumps(clean(view["spec"])))
    assert "<svg" in svg[:300]


def test_unknown_and_nonstats_modules_never_dropped():
    fam, title, _, view = view_for(mod("deseq2counts", {}))
    assert fam == "de" and view["type"] == "raw"
    fam, title, _, view = view_for(mod("totallyunknown", {}))
    assert fam == "other" and view["type"] == "raw"


def test_builder_error_falls_back_to_raw():
    # malformed pca (missing components) must not crash the report
    _, _, _, view = view_for(mod("pca", {}))
    assert view["type"] == "raw"


def test_report_is_self_contained(tmp_path):
    from de_toolkit.report import DetkReport

    rep = DetkReport(str(tmp_path / "rep"), crate_dir=str(tmp_path))
    for name, m in FIXTURES.items():
        with open(os.path.join(rep.json_dir, name + ".json"), "w") as f:
            json.dump(m, f)
    rep.write()

    html = open(rep.report_path, encoding="utf-8").read()
    # no external assets loaded at view time (precise: only tag src/href attrs)
    assert not re.findall(r'<(?:script|link|img)[^>]+(?:src|href)="https?://', html)
    # vendored charting libs inlined
    assert "vegaEmbed" in html
    # embedded payload parses and covers every module
    payload = re.search(r'id="detk-modules">(.*?)</script>', html, re.S).group(1)
    mods = json.loads(payload)
    assert set(FIXTURES).issubset({m["module"] for m in mods})
    # raw provenance payload parses too
    raw = re.search(r'id="detk-raw">(.*?)</script>', html, re.S).group(1)
    json.loads(raw)


# --------------------------------------------------------------------------
# de family (#4/#5)
# --------------------------------------------------------------------------


def de_mod(n_ns=50, n_sig=10, with_mean=True, name="deseq2counts"):
    pts = []
    for i in range(n_sig):
        p = {"feature": f"g{i}", "effect": 2.5, "nlp": 8.0, "sig": "up"}
        if with_mean:
            p["lmean"] = 2.0
        pts.append(p)
    for i in range(n_ns):
        p = {"feature": f"n{i}", "effect": 0.01 * i - 0.25, "nlp": 0.5, "sig": "ns"}
        if with_mean:
            p["lmean"] = 1.5
        pts.append(p)
    return mod(
        name,
        {
            "num_length": n_ns + n_sig,
            "de": {
                "feature_col": "gene",
                "kind": "deseq2" if name == "deseq2counts" else "firth",
                "terms": [
                    {
                        "term": "cond__case",
                        "total": n_ns + n_sig,
                        "shown": n_ns + n_sig,
                        "num_sig": n_sig,
                        "sig_threshold": 0.05,
                        "points": pts,
                    },
                    {
                        "term": "age",
                        "total": n_ns + n_sig,
                        "shown": n_ns + n_sig,
                        "num_sig": 0,
                        "sig_threshold": 0.05,
                        "points": pts[:5],
                    },
                ],
            },
        },
    )


def test_deseq2_view_is_volcano_plus_ma_with_term_dropdown():
    fam, _, _, view = view_for(de_mod())
    assert fam == "de" and view["type"] == "vega"
    spec = view["spec"]
    assert len(spec["vconcat"]) == 2  # volcano + MA
    assert spec["params"][0]["bind"]["options"] == ["cond__case", "age"]
    assert any(r["term"] == "age" for r in spec["data"]["values"])


def test_firth_view_is_volcano_only_without_mean():
    fam, _, _, view = view_for(de_mod(with_mean=False, name="flgcounts"))
    assert fam == "de" and view["type"] == "vega"
    assert len(view["spec"]["vconcat"]) == 1  # no MA without baseMean


def test_de_spec_compiles():
    vlc = pytest.importorskip("vl_convert")
    _, _, _, view = view_for(de_mod())
    svg = vlc.vegalite_to_svg(json.dumps(clean(view["spec"])))
    assert "<svg" in svg[:300]


def test_de_sampling_note_shown_when_capped():
    m = de_mod()
    m["properties"]["de"]["terms"][0]["shown"] = 40
    m["properties"]["de"]["terms"][0]["total"] = 60000
    _, _, _, view = view_for(m)
    assert "density-preserving sample" in view["note"]
    assert "60,000" in view["note"]


def test_de_large_point_set_renders_static_svg():
    from de_toolkit.static_plots import MAX_INTERACTIVE_POINTS

    pytest.importorskip("matplotlib")
    n = MAX_INTERACTIVE_POINTS + 1
    m = de_mod(n_ns=n, n_sig=0)
    _, _, _, view = view_for(m)
    assert view["type"] == "svg"
    assert view["svg"].lstrip().startswith("<?xml") or "<svg" in view["svg"][:500]
    assert "Rendered statically" in view["note"]


def test_de_report_data_caps_and_classifies():
    import pandas as pd

    from de_toolkit.de import DE_POINT_BUDGET, _de_report_data

    n = DE_POINT_BUDGET + 3000
    df = pd.DataFrame(
        {
            "gene": [f"g{i}" for i in range(n)],
            "baseMean": [10.0] * n,
            "cond__log2FoldChange": [2.0 if i < 100 else 0.1 for i in range(n)],
            "cond__pvalue": [1e-10 if i < 100 else 0.5 for i in range(n)],
            "cond__padj": [1e-8 if i < 100 else 0.9 for i in range(n)],
            "Intercept__log2FoldChange": [1.0] * n,
            "Intercept__pvalue": [0.5] * n,
            "Intercept__padj": [0.9] * n,
        }
    )
    de = _de_report_data(df, "deseq2")
    assert de["feature_col"] == "gene"
    assert [t["term"] for t in de["terms"]] == ["cond"]  # Intercept excluded
    t = de["terms"][0]
    assert t["total"] == n and t["num_sig"] == 100
    assert t["shown"] <= DE_POINT_BUDGET
    sigs = [p for p in t["points"] if p["sig"] == "up"]
    assert len(sigs) == 100  # every significant feature survives the cap
    assert all("lmean" in p and "nlp" in p for p in t["points"])
    # deterministic
    assert _de_report_data(df, "deseq2") == de


# --------------------------------------------------------------------------
# norm + transform families (#6/#7)
# --------------------------------------------------------------------------

NORM_TRANSFORM_FIXTURES = {
    "deseq2norm": mod(
        "deseq2norm",
        {"num_kept": 100, "size_factors": {"s1": 0.9, "s2": 1.1, "s3": 1.0}},
    ),
    "librarysize": mod(
        "librarysize",
        {"num_features": 100, "library_sizes": {"s1": 1e6, "s2": 2e6}},
    ),
    "fpkmcounts": mod(
        "fpkmcounts",
        {
            "num_kept": 100,
            "length_quantiles": [{"q": q, "length": 100.0 * (q + 1)} for q in range(0, 101, 5)],
        },
    ),
    "plogcounts": mod(
        "plogcounts",
        {
            "num_length": 100,
            "transform": {
                "dists": [
                    {"stage": st, "sample": s, "q": q, "value": float(q)}
                    for st in ("before", "after")
                    for s in ("s1", "s2")
                    for q in range(0, 101, 5)
                ],
                "mean_sd": [
                    {"stage": st, "rank_pct": float(i), "sd": 1.0}
                    for st in ("before", "after")
                    for i in range(0, 100, 10)
                ],
            },
        },
        params={"pseudocount": 1, "base": 10},
    ),
}
NORM_TRANSFORM_FIXTURES["vstcounts"] = dict(NORM_TRANSFORM_FIXTURES["plogcounts"], name="vstcounts")
NORM_TRANSFORM_FIXTURES["rlogcounts"] = dict(
    NORM_TRANSFORM_FIXTURES["plogcounts"], name="rlogcounts"
)

_EXPECTED_FAMILY = {
    "deseq2norm": "norm",
    "librarysize": "norm",
    "fpkmcounts": "norm",
    "plogcounts": "transform",
    "vstcounts": "transform",
    "rlogcounts": "transform",
}


@pytest.mark.parametrize("name", list(NORM_TRANSFORM_FIXTURES))
def test_view_for_norm_transform_families(name):
    family, title, _, view = view_for(NORM_TRANSFORM_FIXTURES[name])
    assert family == _EXPECTED_FAMILY[name]
    assert view["type"] == "vega"


@pytest.mark.parametrize("name", list(NORM_TRANSFORM_FIXTURES))
def test_norm_transform_specs_compile(name):
    vlc = pytest.importorskip("vl_convert")
    _, _, _, view = view_for(NORM_TRANSFORM_FIXTURES[name])
    svg = vlc.vegalite_to_svg(json.dumps(clean(view["spec"])))
    assert "<svg" in svg[:300]


def test_transform_view_has_before_after_and_meansd():
    _, _, _, view = view_for(NORM_TRANSFORM_FIXTURES["vstcounts"])
    spec = view["spec"]
    assert len(spec["vconcat"]) == 2  # dist facet + mean-sd trend
    assert "variance-stabilizing" in view["note"]


def test_transform_report_data_shapes():
    import pandas as pd

    from de_toolkit.transform import _transform_report_data

    before = pd.DataFrame(
        {"s1": range(100), "s2": range(0, 200, 2)}, index=[f"g{i}" for i in range(100)]
    )
    after = before / 10.0
    t = _transform_report_data(before, after)
    stages = {d["stage"] for d in t["dists"]}
    assert stages == {"before", "after"}
    assert len(t["dists"]) == 2 * 2 * 21  # stages x samples x quantiles
    assert all(0 <= m["rank_pct"] <= 100 for m in t["mean_sd"])
    json.dumps(t)  # serializable


def test_plog_module_emits_transform_data(tmp_path):
    import pandas as pd

    from de_toolkit.common import CountMatrix
    from de_toolkit.transform import PlogCounts

    counts = pd.DataFrame({"s1": [0, 10, 100], "s2": [5, 50, 500]}, index=["g1", "g2", "g3"])
    obj = PlogCounts(CountMatrix(counts))
    props = obj.properties
    assert "transform" in props and props["transform"]["dists"]
    assert obj["params"] == {"pseudocount": 1, "base": 10}


# --------------------------------------------------------------------------
# filter + enrich families (#8/#9)
# --------------------------------------------------------------------------


def test_filtercounts_view_accounts_for_features():
    m = mod(
        "filtercounts",
        {"num_kept": 900, "num_filtered": 100},
        params={"command": "mean(all) > 10"},
    )
    fam, _, _, view = view_for(m)
    assert fam == "filter" and view["type"] == "kv"
    items = {i["label"]: i["value"] for i in view["items"]}
    assert items["features in"] == 1000
    assert items["features kept"] == 900
    assert items["features removed"] == 100
    assert items["kept"] == "90.0%"
    assert "mean(all) > 10" in view["note"]


FGSEA_FIXTURE = mod(
    "fgseares",
    {
        "num_pathways": 500,
        "fgsea": {
            "num_sig": 2,
            "sig_threshold": 0.05,
            "top_n": 3,
            "pathways": [
                {
                    "pathway": "A",
                    "nes": 2.5,
                    "size": 50,
                    "nlpadj": 9.0,
                    "padj_str": "1.00e-09",
                    "sig": True,
                },
                {
                    "pathway": "B",
                    "nes": -1.8,
                    "size": 20,
                    "nlpadj": 1.5,
                    "padj_str": "3.00e-02",
                    "sig": True,
                },
                {
                    "pathway": "C",
                    "nes": 0.3,
                    "size": 10,
                    "nlpadj": 0.3,
                    "padj_str": "5.00e-01",
                    "sig": False,
                },
            ],
        },
    },
)


def test_fgseares_view_is_nes_dotplot():
    fam, _, _, view = view_for(FGSEA_FIXTURE)
    assert fam == "enrich" and view["type"] == "vega"
    assert "Top 3 gene sets" in view["note"]
    assert "500 tested" in view["note"]


def test_fgseares_spec_compiles():
    vlc = pytest.importorskip("vl_convert")
    _, _, _, view = view_for(FGSEA_FIXTURE)
    svg = vlc.vegalite_to_svg(json.dumps(clean(view["spec"])))
    assert "<svg" in svg[:300]


def test_fgsea_report_data_helper():
    import pandas

    from de_toolkit.enrich import _fgsea_report_data

    df = pandas.DataFrame(
        {
            "pathway": [f"P{i}" for i in range(50)],
            "padj": [1e-9] * 5 + [0.5] * 45,
            "NES": [2.0] * 5 + [0.1] * 45,
            "size": [30] * 50,
        }
    )
    fg = _fgsea_report_data(df)
    assert fg["num_sig"] == 5
    assert fg["top_n"] == 30  # capped
    # small padj survives the float-truncating encoder as a string
    assert fg["pathways"][0]["padj_str"] == "1.00e-09"
    assert fg["pathways"][0]["nlpadj"] == 9.0
    json.dumps(fg)


def test_no_module_left_in_fallback():
    """Every known module now has a real builder; the fallback map should be
    empty (it remains as the safety net for future modules)."""
    from de_toolkit.report_specs import _FALLBACK_FAMILIES

    assert _FALLBACK_FAMILIES == {}
