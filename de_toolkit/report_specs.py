r"""
Report view builders for detk modules.

Each detk module serializes to JSON (name/params/properties). This module turns
that JSON into a "view" that the report SPA renders. A view is one of:

- {"type": "vega",  "spec": <Vega-Lite spec dict>}   an interactive chart
- {"type": "kv",    "items": [{"label","value"}...]} summary stat tiles
- {"type": "table", "columns": [...], "rows": [[...]]} a data table
- {"type": "raw"}                                     fall back to raw JSON

Builders are looked up by module name in ``REGISTRY``. Each registry entry
carries the ``family`` (top-level nav grouping), a human ``title``, a short
``desc``, and the ``builder`` callable ``(module_json_dict) -> view``. Unknown
modules fall back to a raw-JSON view so nothing is ever silently dropped (a bug
in the previous report system).
"""

import math

VEGA_LITE_SCHEMA = "https://vega.github.io/schema/vega-lite/v5.json"

# palette shared with the report template's category range
_CAT = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2", "#ff9da6"]


def clean(obj):
    """Replace non-finite floats (NaN/Inf) with None so the embedded payload is
    valid JSON (browser JSON.parse and strict validators reject bare NaN)."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return obj


def _vl(spec):
    spec.setdefault("$schema", VEGA_LITE_SCHEMA)
    spec.setdefault("width", "container")
    spec.setdefault("height", 340)
    return {"type": "vega", "spec": spec}


# ---------------------------------------------------------------------------
# stats module builders
# ---------------------------------------------------------------------------


def build_basestats(mod):
    p = mod["properties"]
    return {
        "type": "kv",
        "items": [
            {"label": "features (rows)", "value": p.get("num_rows")},
            {"label": "samples (columns)", "value": p.get("num_cols")},
        ],
    }


def build_pca(mod):
    p = mod["properties"]
    comps = p["components"]
    if len(comps) < 2:
        return {"type": "raw"}
    pc1, pc2 = comps[0], comps[1]
    cv = p["column_variables"]
    samples = cv["sample_names"]
    covs = {c["column"]: c["values"] for c in cv["columns"]}
    rows = []
    for i, s in enumerate(samples):
        row = {"sample": s, "PC1": pc1["scores"][i], "PC2": pc2["scores"][i]}
        for cname, vals in covs.items():
            row[cname] = vals[i]
        rows.append(row)
    color_field = "status" if "status" in covs else (list(covs)[0] if covs else None)
    tooltip = [
        {"field": "sample", "title": "sample"},
        {"field": "PC1", "type": "quantitative", "format": ".2f"},
        {"field": "PC2", "type": "quantitative", "format": ".2f"},
    ]
    tooltip += [{"field": c, "title": c} for c in covs]
    enc = {
        "x": {
            "field": "PC1",
            "type": "quantitative",
            "title": "PC1 ({:.1f}% variance)".format(100 * pc1["perc_variance"]),
        },
        "y": {
            "field": "PC2",
            "type": "quantitative",
            "title": "PC2 ({:.1f}% variance)".format(100 * pc2["perc_variance"]),
        },
        "tooltip": tooltip,
    }
    if color_field is not None:
        enc["color"] = {"field": color_field, "type": "nominal", "title": color_field}
    return _vl(
        {
            "data": {"values": rows},
            "mark": {"type": "point", "filled": True, "size": 110, "opacity": 0.85},
            "encoding": enc,
        }
    )


def build_entropy(mod):
    e = mod["properties"]["entropies"]
    rows = [{"pct": pct, "entropy": val} for pct, val in zip(e["pct"], e["pctVal"])]
    thresh = 5
    ymax = max((r["entropy"] for r in rows if r["entropy"] is not None), default=0)
    return _vl(
        {
            "data": {"values": rows},
            "layer": [
                {
                    "mark": {"type": "area", "opacity": 0.25, "color": _CAT[0]},
                    "encoding": {
                        "x": {"field": "pct", "type": "quantitative"},
                        "y": {"field": "entropy", "type": "quantitative"},
                    },
                },
                {
                    "mark": {"type": "line", "color": _CAT[0]},
                    "encoding": {
                        "x": {
                            "field": "pct",
                            "type": "quantitative",
                            "title": "feature percentile",
                        },
                        "y": {
                            "field": "entropy",
                            "type": "quantitative",
                            "title": "Shannon entropy",
                        },
                    },
                },
                {
                    "mark": {"type": "rule", "color": _CAT[3], "strokeDash": [5, 4]},
                    "encoding": {"x": {"datum": thresh}},
                },
                {
                    "mark": {
                        "type": "text",
                        "align": "left",
                        "dx": 5,
                        "dy": -6,
                        "color": _CAT[3],
                        "fontSize": 11,
                    },
                    "encoding": {
                        "x": {"datum": thresh},
                        "y": {"datum": ymax},
                        "text": {"datum": f"p{thresh} threshold"},
                    },
                },
            ],
        }
    )


def build_colzero(mod):
    rows = [{"sample": z["name"], "zero_frac": z["zero_frac"]} for z in mod["properties"]["zeros"]]
    return _vl(
        {
            "data": {"values": rows},
            "mark": {"type": "bar", "color": _CAT[2]},
            "encoding": {
                "x": {"field": "sample", "type": "nominal", "sort": "-y", "title": "sample"},
                "y": {
                    "field": "zero_frac",
                    "type": "quantitative",
                    "title": "fraction of zero counts",
                    "axis": {"format": "%"},
                },
                "tooltip": [
                    {"field": "sample"},
                    {"field": "zero_frac", "type": "quantitative", "format": ".1%"},
                ],
            },
            "height": 300,
        }
    )


def build_rowzero(mod):
    rows = [
        {
            "num_zeros": z["num_zeros"],
            "num_features": z["num_features"],
            "feature_frac": z["feature_frac"],
        }
        for z in mod["properties"]["zeros"]
    ]
    return _vl(
        {
            "data": {"values": rows},
            "mark": {"type": "bar", "color": _CAT[0]},
            "encoding": {
                "x": {
                    "field": "num_zeros",
                    "type": "ordinal",
                    "title": "number of zero-count samples",
                },
                "y": {
                    "field": "num_features",
                    "type": "quantitative",
                    "title": "number of features",
                },
                "tooltip": [
                    {"field": "num_zeros", "title": "zeros"},
                    {"field": "num_features", "title": "features"},
                    {"field": "feature_frac", "type": "quantitative", "format": ".1%"},
                ],
            },
            "height": 300,
        }
    )


def build_coldist(mod):
    # per-column count distribution as a quantile curve (value vs percentile),
    # overlaid across samples. symlog y handles the zero-inflated count range
    # without the raw-count histogram looking like a single spike.
    rows = []
    for d in mod["properties"]["dists"]:
        name = d["name"]
        for frac, val in d["percentiles"]:
            rows.append({"sample": name, "quantile": frac, "value": val})
    return _vl(
        {
            "data": {"values": rows},
            "mark": {"type": "line", "opacity": 0.6, "strokeWidth": 1.5},
            "encoding": {
                "x": {
                    "field": "quantile",
                    "type": "quantitative",
                    "title": "quantile",
                    "axis": {"format": "%"},
                },
                "y": {
                    "field": "value",
                    "type": "quantitative",
                    "title": "count",
                    "scale": {"type": "symlog", "constant": 1},
                },
                "color": {"field": "sample", "type": "nominal", "legend": {"title": "sample"}},
                "tooltip": [
                    {"field": "sample"},
                    {"field": "quantile", "type": "quantitative", "format": ".0%"},
                    {"field": "value", "type": "quantitative", "format": ".0f"},
                ],
            },
        }
    )


def build_rowdist(mod):
    # per-feature distributions across samples; there are far too many features
    # to draw individually, so overlay a deterministic sample of them as faint
    # lines to convey the spread of feature distribution shapes.
    dists = mod["properties"]["dists"]
    n = len(dists)
    step = max(1, n // 60)
    rows = []
    for idx in range(0, n, step):
        d = dists[idx]
        binvals = d.get("bins") or []
        counts = d.get("dist") or []
        for j, c in enumerate(counts):
            if j < len(binvals):
                rows.append({"feature": d["name"], "value": binvals[j], "count": c})
    n_shown = len({r["feature"] for r in rows})
    return _vl(
        {
            "title": {
                "text": f"sample of {n_shown} of {n} features",
                "fontSize": 11,
                "color": "#888",
                "anchor": "start",
            },
            "data": {"values": rows},
            "mark": {"type": "line", "opacity": 0.18, "strokeWidth": 1, "color": _CAT[5]},
            "encoding": {
                "x": {
                    "field": "value",
                    "type": "quantitative",
                    "title": "count",
                    "scale": {"type": "symlog", "constant": 1},
                },
                "y": {"field": "count", "type": "quantitative", "title": "features per bin"},
                "detail": {"field": "feature"},
            },
        }
    )


# ---------------------------------------------------------------------------
# outlier module builders
# ---------------------------------------------------------------------------


def build_entropycounts(mod):
    """Entropy percentile curve with the module's actual threshold marked
    (the stats-family entropy chart shows an example threshold instead)."""
    e = mod["properties"]["entropies"]
    rows = [{"pct": pct, "entropy": val} for pct, val in zip(e["pct"], e["pctVal"])]
    thresh = mod.get("params", {}).get("threshold")
    flagged = mod["properties"].get("num_flagged")
    ymax = max((r["entropy"] for r in rows if r["entropy"] is not None), default=0)
    label = f"p{thresh} threshold" + (f" ({flagged} flagged)" if flagged is not None else "")
    return _vl(
        {
            "data": {"values": rows},
            "layer": [
                {
                    "mark": {"type": "area", "opacity": 0.25, "color": _CAT[0]},
                    "encoding": {
                        "x": {"field": "pct", "type": "quantitative"},
                        "y": {"field": "entropy", "type": "quantitative"},
                    },
                },
                {
                    "mark": {"type": "line", "color": _CAT[0]},
                    "encoding": {
                        "x": {
                            "field": "pct",
                            "type": "quantitative",
                            "title": "feature percentile",
                        },
                        "y": {
                            "field": "entropy",
                            "type": "quantitative",
                            "title": "Shannon entropy",
                        },
                    },
                },
                {
                    "mark": {"type": "rule", "color": _CAT[3], "strokeDash": [5, 4]},
                    "encoding": {"x": {"datum": thresh}},
                },
                {
                    "mark": {
                        "type": "text",
                        "align": "left",
                        "dx": 5,
                        "dy": -6,
                        "color": _CAT[3],
                        "fontSize": 11,
                    },
                    "encoding": {
                        "x": {"datum": thresh},
                        "y": {"datum": ymax},
                        "text": {"datum": label},
                    },
                },
            ],
        }
    )


def build_shrink(mod):
    p = mod.get("params", {})
    props = mod.get("properties", {})
    return {
        "type": "kv",
        "items": [
            {"label": "features", "value": props.get("num_kept")},
            {"label": "shrink factor", "value": p.get("shrink_factor")},
            {"label": "max sample proportion (p_max)", "value": p.get("p_max") or "sqrt(1/n)"},
            {"label": "iterations", "value": p.get("iters")},
        ],
    }


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

REGISTRY = {
    # stats family
    "basestats": ("stats", "Basic statistics", "Feature and sample counts.", build_basestats),
    "coldist": (
        "stats",
        "Column count distribution",
        "Per-sample count distribution shown as quantile curves (symlog scale).",
        build_coldist,
    ),
    "rowdist": (
        "stats",
        "Row count distribution",
        "Per-feature count distributions across samples (sampled overlay).",
        build_rowdist,
    ),
    "colzero": (
        "stats",
        "Zero counts by sample",
        "Fraction of features with exactly zero counts in each sample.",
        build_colzero,
    ),
    "rowzero": (
        "stats",
        "Zero counts by feature",
        "How many features have a given number of zero-count samples.",
        build_rowzero,
    ),
    "entropy": (
        "stats",
        "Feature entropy",
        "Shannon entropy across feature percentiles with an example low-entropy threshold.",
        build_entropy,
    ),
    "pca": (
        "stats",
        "Principal component analysis",
        "Samples on the first two principal components, coloured by a covariate.",
        build_pca,
    ),
    # outlier family
    "entropycounts": (
        "outlier",
        "Entropy outlier flagging",
        "Shannon entropy across feature percentiles with the flagging threshold marked.",
        build_entropycounts,
    ),
    "shrinkcounts": (
        "outlier",
        "Outlier count shrinkage",
        "Counts dominating a feature's mass shrunk toward the feature distribution.",
        build_shrink,
    ),
    "pmftransform": (
        "outlier",
        "PMF transform",
        "Probability-mass-function transform underlying outlier count shrinkage.",
        build_shrink,
    ),
}

# families for non-stats modules so nav grouping works and they are not dropped;
# builders are added in later phases (they fall back to a raw-JSON view for now).
_FALLBACK_FAMILIES = {
    "deseq2counts": ("de", "DESeq2 differential expression"),
    "flgcounts": ("de", "Firth logistic differential expression"),
    "deseq2norm": ("norm", "DESeq2 normalization"),
    "librarysize": ("norm", "Library-size normalization"),
    "fpkmcounts": ("norm", "FPKM normalization"),
    "plogcounts": ("transform", "Pseudo-log transform"),
    "vstcounts": ("transform", "Variance-stabilizing transform"),
    "rlogcounts": ("transform", "Regularized-log transform"),
    "filtercounts": ("filter", "Feature filter"),
    "fgseares": ("enrich", "fgsea gene-set enrichment"),
}


def view_for(mod):
    """Return (family, title, desc, view) for a module JSON dict."""
    name = mod.get("name", "unknown")
    if name in REGISTRY:
        family, title, desc, builder = REGISTRY[name]
        try:
            view = builder(mod)
        except Exception as e:  # never let one bad module break the whole report
            view = {"type": "raw", "error": str(e)}
        return family, title, desc, view
    if name in _FALLBACK_FAMILIES:
        family, title = _FALLBACK_FAMILIES[name]
        return family, title, "Interactive view coming in a later release.", {"type": "raw"}
    return "other", name, "", {"type": "raw"}
