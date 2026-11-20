"""Module JSON, the report's embedded payload and the provenance crate are
strictly valid JSON (#116): a missing or non-finite number is null, never the
bare NaN or Infinity that strict parsers (jq, JSON.parse) reject.

The end-to-end tests run every detk subcommand that writes a module JSON as a
console script, on fixture data that yields missing values where a module can
produce them, and read everything back with a strict parser. The R-backed
subcommands run where R and their packages are installed (the R job in CI).
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
from importlib.resources import files as pkg_files

import numpy as np
import pandas as pd
import pytest

from de_toolkit.crate import CRATE_FILENAME, finite_json, write_crate
from de_toolkit.report import DetkReport, NumpyEncoder, script_json
from de_toolkit.report_specs import clean, view_for
from de_toolkit.wrapr import check_r_package

HERE = os.path.dirname(os.path.abspath(__file__))
GATHER = os.path.join(HERE, os.pardir, "util", "data", "gather", "htseq")


def _reject(token):
    raise ValueError(f"not strict JSON: bare {token}")


def strict_loads(text):
    "json.loads that refuses NaN, Infinity and -Infinity, as jq and JSON.parse do"
    return json.loads(text, parse_constant=_reject)


def _nulls(obj, path=""):
    "Every path in *obj* that holds null"
    if obj is None:
        return [path]
    if isinstance(obj, dict):
        return [p for k, v in obj.items() for p in _nulls(v, f"{path}/{k}")]
    if isinstance(obj, list):
        return [p for i, v in enumerate(obj) for p in _nulls(v, f"{path}[{i}]")]
    return []


# --------------------------------------------------------------------------
# the encoder
# --------------------------------------------------------------------------

NAN, INF = float("nan"), float("inf")

NONFINITE = [
    NAN,
    INF,
    -INF,
    np.float64("nan"),
    np.float32("nan"),
    np.float16("inf"),
    np.float64("-inf"),
]


@pytest.mark.parametrize("value", NONFINITE, ids=repr)
@pytest.mark.parametrize(
    "wrap",
    [
        lambda v: v,
        lambda v: [1.0, v],
        lambda v: (v,),
        lambda v: {"a": {"b": [{"c": v}]}},
        lambda v: np.array([1.0, v]),
        lambda v: {"m": np.array([[v, 2.0], [3.0, v]])},
    ],
    ids=["bare", "list", "tuple", "nested", "array", "array2d"],
)
def test_encoder_writes_nonfinite_as_null(value, wrap):
    obj = wrap(value)
    for text in (json.dumps(obj, cls=NumpyEncoder), script_json(obj)):
        assert "NaN" not in text and "Infinity" not in text and "inf" not in text
        parsed = strict_loads(text)
        assert _nulls(parsed)
    # json.dump goes through iterencode, not encode
    buf = io.StringIO()
    json.dump(obj, buf, cls=NumpyEncoder, indent=2)
    assert _nulls(strict_loads(buf.getvalue()))


def test_encoder_dataframe_derived_lists():
    df = pd.DataFrame({"x": [1.0, np.nan, 3.0], "y": [np.inf, 2.0, -np.inf], "s": ["a", "b", None]})
    obj = {
        "records": df.to_dict("records"),
        "values": df[["x", "y"]].values.tolist(),
        "array": df[["x", "y"]].to_numpy(),
        "series": df["x"].tolist(),
    }
    for text in (json.dumps(obj, cls=NumpyEncoder), script_json(obj)):
        parsed = strict_loads(text)
        assert parsed["records"][1]["x"] is None
        assert parsed["records"][0]["y"] is None and parsed["records"][2]["y"] is None
        assert parsed["values"][1] == [None, 2.0]
        assert parsed["array"][2] == [3.0, None]
        assert parsed["series"] == [1.0, None, 3.0]


def test_encoder_keeps_finite_values():
    d = {"i": np.int64(3), "f": np.float32(2.5), "b": np.bool_(True), "s": "x", "n": None}
    assert strict_loads(json.dumps(d, cls=NumpyEncoder)) == {
        "b": True,
        "f": 2.5,
        "i": 3,
        "n": None,
        "s": "x",
    }
    # the payload rounding is unchanged
    assert json.dumps([1.2039820493842, NAN], cls=NumpyEncoder) == "[1.204, null]"


def test_encoder_refuses_bare_nonfinite():
    # allow_nan=False whatever the caller asks for: a non-finite float that
    # slipped past the null conversion is an error, never bare NaN
    assert NumpyEncoder(allow_nan=True).allow_nan is False
    with pytest.raises(ValueError):
        json.JSONEncoder.iterencode(NumpyEncoder(), [NAN], _one_shot=True).__next__()


def test_finite_json():
    assert finite_json({"a": [NAN, (1, np.float64(INF))], "b": np.array([np.nan])}) == {
        "a": [None, [1, None]],
        "b": [None],
    }
    assert finite_json(True) is True and finite_json(np.int32(2)) == 2


def test_crate_is_strict(tmp_path):
    doc = {
        "name": "pca",
        "id": "x",
        "params": {"alpha": NAN, "list": [1.0, INF]},
        "properties": {},
        "in_file_path": "counts.csv",
        "workdir": str(tmp_path),
    }
    path = write_crate([doc], str(tmp_path))
    crate = strict_loads(open(path).read())
    values = [e.get("value") for e in crate["@graph"] if e.get("@type") == "PropertyValue"]
    assert None in values and "[1.0, null]" in values


# --------------------------------------------------------------------------
# every module, end to end
# --------------------------------------------------------------------------


def _run(args, cwd):
    "Run a detk console script as a subprocess, as a user would"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    assert p.returncode == 0, (
        f"{' '.join(args)} failed with code {p.returncode}\n"
        f"stdout:\n{p.stdout}\nstderr:\n{p.stderr}"
    )


GENES = [f"g{i:02d}" for i in range(40)]
SAMPLES = [f"s{i}" for i in range(1, 9)]


def _stage(d):
    "Fixture data: counts with an all-zero and a mostly-zero row, sample info with a missing value"
    rng = np.random.default_rng(116)
    counts = rng.negative_binomial(5, 0.05, size=(len(GENES), len(SAMPLES)))
    counts[3] = 0  # all zero: rowzero's means and medians are missing
    counts[4] = [0, 0, 0, 0, 0, 0, 0, 7]
    df = pd.DataFrame(counts, index=GENES, columns=SAMPLES).rename_axis("gene")
    df.to_csv(d / "counts.csv")
    df.drop(index=GENES[3]).to_csv(d / "counts_nonzero.csv")
    pd.DataFrame(
        {
            "sample": SAMPLES,
            "group": ["a"] * 4 + ["b"] * 4,
            # a missing value under --color-col
            "batch": ["x", None, "y", "x", "y", "x", "y", "x"],
            "category": [0, 1, 0, 1, 0, 1, 1, 0],
        }
    ).to_csv(d / "info.csv", index=False)
    pd.DataFrame({"gene": GENES, "length": rng.integers(500, 5000, len(GENES))}).to_csv(
        d / "lengths.csv", index=False
    )
    pd.DataFrame(
        {
            "gene": GENES,
            "log2FoldChange": np.where(np.arange(40) % 9 == 0, np.nan, rng.normal(size=40)),
            "padj": np.where(np.arange(40) % 7 == 0, np.nan, rng.uniform(size=40)),
        }
    ).to_csv(d / "result.csv", index=False)
    pd.DataFrame({"gene": GENES[:30], "symbol": [f"SYM{i}" for i in range(30)]}).to_csv(
        d / "mapping.csv", index=False
    )
    with open(d / "sets.gmt", "w") as f:
        for i in range(4):
            f.write("\t".join([f"set{i}", "desc", *GENES[i * 10 : i * 10 + 10]]) + "\n")
    for fn in os.listdir(GATHER):
        if fn.startswith(("s1", "s2")):
            shutil.copy(os.path.join(GATHER, fn), d / fn)


# each subcommand that writes a module JSON, with arguments; the R-backed
# ones name the R package they need
PY_COMMANDS = [
    ["detk-stats", "summary", "--color-col", "batch", "-o", "o.csv", "counts.csv", "info.csv"],
    ["detk-stats", "basestats", "-o", "o.csv", "counts.csv"],
    ["detk-stats", "coldist", "-o", "o.csv", "counts.csv"],
    ["detk-stats", "rowdist", "-o", "o.csv", "counts.csv"],
    ["detk-stats", "colzero", "-o", "o.csv", "counts.csv"],
    ["detk-stats", "rowzero", "-o", "o.csv", "counts.csv"],
    ["detk-stats", "entropy", "-o", "o.csv", "counts.csv"],
    ["detk-stats", "pca", "-o", "o.csv", "counts.csv", "info.csv"],
    ["detk-norm", "deseq2", "-o", "o.csv", "counts.csv"],
    ["detk-norm", "library", "-o", "o.csv", "counts.csv"],
    ["detk-norm", "cpm", "-o", "o.csv", "counts.csv"],
    ["detk-norm", "fpkm", "-o", "o.csv", "counts.csv", "lengths.csv"],
    ["detk-norm", "tpm", "-o", "o.csv", "counts.csv", "lengths.csv"],
    ["detk-transform", "plog", "-o", "o.csv", "counts.csv"],
    ["detk-filter", "-o", "o.csv", "mean(all) > 10", "counts.csv"],
    ["detk-filter", "-o", "o.csv", "nonzero(group) > 0.5", "counts.csv", "info.csv"],
    # on counts without the all-zero row: entropy fails on one, before
    # writing anything (a bug of its own, outside this test)
    ["detk-outlier", "entropy", "-p", "0.05", "-o", "o.csv", "counts_nonzero.csv"],
    ["detk-outlier", "shrink", "-o", "o.csv", "counts.csv"],
    # tidy, tidy-counts and tidy-covs write no module JSON
    ["detk-util", "annotate", "-o", "o.csv", "result.csv", "mapping.csv"],
    ["detk-util", "gather", "-o", "o.csv", "s1.counts.txt", "s2.counts.txt"],
    [
        "detk-util",
        "record",
        "-i",
        "counts.csv",
        "-o",
        "copy.csv",
        "--tool-version",
        "1",
        "--",
        sys.executable,
        "-c",
        "import shutil; shutil.copy('counts.csv', 'copy.csv')",
    ],
]

# the module of every subcommand above
PY_MODULES = {
    "annotate",
    "basestats",
    "coldist",
    "colzero",
    "cpmcounts",
    "deseq2norm",
    "entropy",
    "entropycounts",
    "filtercounts",
    "fpkmcounts",
    "gather",
    "librarysize",
    "pca",
    "plogcounts",
    "record",
    "rowdist",
    "rowzero",
    "shrinkcounts",
    "tpmcounts",
}

R_COMMANDS = [
    ("DESeq2", ["detk-transform", "vst", "-o", "o.csv", "counts.csv"]),
    ("DESeq2", ["detk-transform", "rlog", "-o", "o.csv", "counts.csv"]),
    ("DESeq2", ["detk-de", "deseq2", "-o", "o.csv", "counts ~ group", "counts.csv", "info.csv"]),
    # an all-zero feature is a singular predictor for logistf
    (
        "logistf",
        ["detk-de", "firth", "-o", "o.csv", "category ~ counts", "counts_nonzero.csv", "info.csv"],
    ),
    (
        "fgsea",
        [
            "detk-enrich",
            "fgsea",
            "--minSize",
            "2",
            "--nperm",
            "100",
            "-i",
            "gene",
            "-c",
            "log2FoldChange",
            "-o",
            "o.csv",
            "sets.gmt",
            "result.csv",
        ],
    ),
]


def _check_report_dir(d, expected_modules):
    "Strict-parse every module JSON and the crate, validate against the schema"
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(pkg_files("de_toolkit").joinpath("module_schema.json").read_text())
    docs = {}
    for fn in sorted((d / "detk_report" / "json").glob("*.json")):
        doc = strict_loads(fn.read_text())
        jsonschema.validate(doc, schema)
        docs.setdefault(doc["name"], []).append(doc)
    assert expected_modules <= set(docs), expected_modules - set(docs)
    strict_loads((d / CRATE_FILENAME).read_text())
    html = (d / "detk_report" / "detk_report.html").read_text()
    for el in ("detk-modules", "detk-raw"):
        payload = re.search(rf'id="{el}">(.*?)</script>', html, re.S).group(1)
        strict_loads(payload)
    return docs


def _run_all(d, commands):
    """Run each command; each must write a module JSON to the report directory
    (a new one, or one rewritten: a subcommand run by summary before has the
    same id)"""
    jdir = d / "detk_report" / "json"

    def stamps():
        return {p: p.stat().st_mtime_ns for p in jdir.glob("*.json")} if jdir.exists() else {}

    for args in commands:
        before = stamps()
        _run(args, d)
        after = stamps()
        written = [p for p, t in after.items() if before.get(p) != t]
        assert written, f"{' '.join(args[:2])} wrote no module JSON"


def test_every_module_writes_strict_json(tmp_path):
    _stage(tmp_path)
    _run_all(tmp_path, PY_COMMANDS)
    docs = _check_report_dir(tmp_path, PY_MODULES)
    # the fixture data does yield missing values where the modules can
    # produce them: they are null, not dropped
    rowzero = [p for doc in docs["rowzero"] for p in _nulls(doc["properties"])]
    assert any(p.endswith("/mean") for p in rowzero), rowzero
    for name in ("coldist", "colzero", "pca"):
        colored = [doc for doc in docs[name] if "color_by" in doc["properties"]]
        assert colored, name
        assert colored[0]["properties"]["color_by"]["values"]["s2"] is None
    pca = [p for doc in docs["pca"] for p in _nulls(doc["properties"])]
    assert any("column_variables" in p for p in pca), pca

    # every view still builds from the documents with nulls in them
    for name, ds in docs.items():
        for doc in ds:
            _, _, _, view = view_for(doc)
            assert "error" not in view, (name, view)


R_PACKAGES = {pkg for pkg, _ in R_COMMANDS}


@pytest.mark.skipif(
    not all(check_r_package(p) for p in R_PACKAGES),
    reason=f"R packages {sorted(R_PACKAGES)} are not all installed",
)
def test_every_r_module_writes_strict_json(tmp_path):
    _stage(tmp_path)
    _run_all(tmp_path, [args for _, args in R_COMMANDS])
    docs = _check_report_dir(
        tmp_path, {"vstcounts", "rlogcounts", "deseq2counts", "flgcounts", "fgseares"}
    )
    for name, ds in docs.items():
        for doc in ds:
            _, _, _, view = view_for(doc)
            assert "error" not in view, (name, view)


# --------------------------------------------------------------------------
# report directories written before: bare NaN in module JSON
# --------------------------------------------------------------------------

OLD_DOCS = {
    # as 0.x and earlier main wrote them, bare NaN and inf included
    "rowzero": '{"name": "rowzero", "id": "a", "detk_version": "0.9.12", '
    '"last_modified": 1, "in_file_path": "counts.csv", "out_file_path": null, '
    '"params": {}, "properties": {"zeros": [{"num_zeros": 0, "num_features": 5, '
    '"feature_frac": 0.5, "mean": NaN, "median": NaN, "nonzero_mean": NaN, '
    '"nonzero_median": NaN}]}}',
    "pca": '{"name": "pca", "id": "b", "detk_version": "0.9.12", "last_modified": 1, '
    '"in_file_path": "counts.csv", "params": {"alpha": NaN}, "properties": '
    '{"column_names": ["s1", "s2", "s3"], "column_variables": {"sample_names": '
    '["s1", "s2", "s3"], "columns": [{"column": "status", "values": ["A", NaN, "B"]}]}, '
    '"components": [{"name": "PC1", "scores": [1.0, -Infinity, 0.5], '
    '"perc_variance": 0.4, "projections": []}, {"name": "PC2", "scores": '
    '[0.2, 0.1, NaN], "perc_variance": 0.2, "projections": []}]}}',
}


def test_old_report_dir_with_bare_nan_rerenders(tmp_path):
    from de_toolkit.report import main

    rdir = tmp_path / "detk_report"
    (rdir / "json").mkdir(parents=True)
    for name, text in OLD_DOCS.items():
        (rdir / "json" / f"{name}.json").write_text(text)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        main(["detk-report", "generate", f"--report-dir={rdir}"])
    finally:
        os.chdir(cwd)

    html = (rdir / "detk_report.html").read_text()
    mods = strict_loads(re.search(r'id="detk-modules">(.*?)</script>', html, re.S).group(1))
    raw = strict_loads(re.search(r'id="detk-raw">(.*?)</script>', html, re.S).group(1))
    assert {m["module"] for m in mods} >= {"rowzero", "pca"}
    assert all(m["view"]["type"] == "vega" for m in mods)
    assert _nulls(raw)
    strict_loads((tmp_path / CRATE_FILENAME).read_text())


# --------------------------------------------------------------------------
# the views render nulls
# --------------------------------------------------------------------------


def _mod(name, properties):
    return {"name": name, "params": {}, "properties": properties, "in_file_path": "c.csv"}


NULL_MODS = {
    "rowzero": _mod(
        "rowzero",
        {
            "zeros": [
                {"num_zeros": 0, "num_features": 5, "feature_frac": 0.5, "mean": 2.0},
                {"num_zeros": 3, "num_features": 1, "feature_frac": 0.1, "mean": None},
            ]
        },
    ),
    "colzero": _mod(
        "colzero",
        {
            "zeros": [{"name": "s1", "zero_frac": 0.1}, {"name": "s2", "zero_frac": None}],
            "color_by": {"column": "dose", "values": {"s1": 1.5, "s2": None}},
        },
    ),
    "pca": _mod(
        "pca",
        {
            "column_names": ["s1", "s2", "s3"],
            "column_variables": {
                "sample_names": ["s1", "s2", "s3"],
                "columns": [{"column": "status", "values": ["A", None, "B"]}],
            },
            "components": [
                {"name": "PC1", "scores": [1.0, None, 0.5], "perc_variance": 0.4},
                {"name": "PC2", "scores": [0.2, 0.1, None], "perc_variance": 0.2},
            ],
            "color_by": {"column": "status", "values": {"s1": "A", "s2": None, "s3": "B"}},
        },
    ),
    "basestats": _mod("basestats", {"num_rows": None, "num_cols": 3}),
}


@pytest.mark.parametrize("name", list(NULL_MODS))
def test_views_with_nulls_compile(name):
    _, _, _, view = view_for(NULL_MODS[name])
    assert "error" not in view
    if view["type"] != "vega":
        return
    vlc = pytest.importorskip("vl_convert")
    svg = vlc.vegalite_to_svg(json.dumps(clean(view["spec"]), allow_nan=False))
    assert "<svg" in svg[:300]


def test_numeric_color_with_a_missing_value_stays_quantitative():
    _, _, _, view = view_for(NULL_MODS["colzero"])
    text = json.dumps(view["spec"])
    assert '"type": "quantitative", "title": "dose"' in text


def test_static_fallback_skips_null_points():
    pytest.importorskip("matplotlib")
    from de_toolkit.static_plots import scatter_svg

    rows = [
        {"effect": 1.0, "nlp": 2.0, "sig": "up"},
        {"effect": None, "nlp": 3.0, "sig": "up"},
        {"effect": -1.0, "nlp": None, "sig": "down"},
        {"effect": 0.1, "nlp": 0.2, "sig": "ns"},
    ]
    svg = scatter_svg(rows, "effect", "nlp", "effect", "-log10 p")
    assert "<svg" in svg


def test_report_with_nulls_writes_strict_payload(tmp_path):
    rep = DetkReport(str(tmp_path / "rep"), crate_dir=str(tmp_path))
    for name, m in NULL_MODS.items():
        with open(os.path.join(rep.json_dir, name + ".json"), "w") as f:
            json.dump(m, f, allow_nan=False)
    rep.write()
    html = open(rep.report_path, encoding="utf-8").read()
    mods = strict_loads(re.search(r'id="detk-modules">(.*?)</script>', html, re.S).group(1))
    assert {m["module"] for m in mods} == set(NULL_MODS)
    assert all(m["view"]["type"] != "raw" for m in mods)
