"""Checks of docs/recipes/covariates.md, the Miller recipes for derived
covariates (DETK-0051 Option C, DETK-0062), too deep to show on the page.

The page itself runs as a tutorial (tests/tutorials, DETK-0064). Here:

- the derived values against numpy (the z-score's sd over n - 1) and, where
  R is installed, against R's ``scale()``;
- the sample names and the other columns as written (``007`` stays ``007``,
  DETK-0015);
- every failure DETK-0062 item 2 lists, run with the page's own recipe
  commands on a bad sheet: non-zero exit, the samples named on stderr, no
  output file and no module JSON;
- that ``detk-util record`` wrote a module JSON naming ``mlr`` and its version;
- that the skill's recipes are the page's, and the formula error's pointer.

Miller is not a detk dependency: the tests that run it skip where ``mlr`` is
absent, and the CI job with R installs it (and fails rather than skips).
"""

import json
import re
import subprocess

import numpy as np
import pandas as pd
import pytest
from recipes_support import require
from tutorial_runner import DOCS, REPO, parse

PAGE = DOCS / "recipes" / "covariates.md"
SKILL = REPO / "skills" / "detk" / "SKILL.md"
SKILL_REF = REPO / "skills" / "detk" / "references" / "covariates.md"
PAGE_URL = "https://bu-neuromics.github.io/de_toolkit/recipes/covariates/"

SAMPLES = ["007", "008", "009", "010", "011", "012"]

# the derived column of each recipe (DETK-0062 item 3), the source column the
# page derives it from, and its value from that column
EXPECTED = {
    "study": ("study", None),
    "conc_log2": ("conc", np.log2),
    "conc_log10": ("conc", np.log10),
    "conc_ln": ("conc", np.log),
    "dose_log2_pc1": ("dose", lambda x: np.log2(x + 1)),
    "age_zscore": ("age", lambda x: (x - x.mean()) / x.std(ddof=1)),
    "age_center": ("age", lambda x: x - x.mean()),
    "age_minmax": ("age", lambda x: (x - x.min()) / (x.max() - x.min())),
}

GOOD = """\
sample,condition,conc,dose,age
007,control,52.0,0,34
008,control,118.5,0,51
009,control,87.2,0,45
010,treated,64.9,10,38
011,treated,230.1,30,62
012,treated,41.3,100,29
"""


def recipes():
    """{derived column: the page's bash block that derives it from
    sample_info.csv}"""
    found = {}
    for block in parse(PAGE).blocks:
        if block.lang != "bash" or block.fails or "detk-util record" not in block.code:
            continue
        m = re.search(r"-o sample_info\.(\S+)\.csv", block.code)
        assert m, f"{PAGE.name}:{block.line}: a recipe without a sample_info.<column>.csv output"
        found[m.group(1)] = block.code
    return found


def read(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def test_the_page_has_a_recipe_for_each_operation():
    assert sorted(recipes()) == sorted(EXPECTED)
    text = PAGE.read_text()
    assert "<!-- tutorial: requires mlr -->" in text
    for name in EXPECTED:
        assert "__" not in name


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_values_match_numpy(name, page_workdir):
    workdir = page_workdir(PAGE)
    source, f = EXPECTED[name]
    out = read(workdir / f"sample_info.{name}.csv")
    assert list(out.columns)[-1] == name
    if f is None:
        assert (out[name] == "pilot").all()
        return
    x = out[source].astype(float)
    np.testing.assert_allclose(out[name].astype(float), f(x), rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_ids_and_columns_as_written(name, page_workdir):
    workdir = page_workdir(PAGE)
    original = read(workdir / "sample_info.csv")
    out = read(workdir / f"sample_info.{name}.csv")
    assert list(out["sample"]) == SAMPLES
    assert list(out.columns) == [*original.columns, name]
    pd.testing.assert_frame_equal(out[original.columns], original)


def test_record_wrote_a_module_json_naming_mlr(page_workdir):
    workdir = page_workdir(PAGE)
    version = subprocess.run(["mlr", "--version"], capture_output=True, text=True).stdout
    docs = [json.loads(p.read_text()) for p in (workdir / "detk_report" / "json").glob("*.json")]
    by_output = {d["out_file_path"]: d for d in docs if d["name"] == "record"}
    # one per recipe; the recipe that failed on the page recorded nothing
    assert sorted(by_output) == sorted(f"sample_info.{n}.csv" for n in EXPECTED)
    for doc in by_output.values():
        assert doc["params"]["tool"] == "mlr"
        assert doc["params"]["tool_version"] == version.splitlines()[0]
        assert doc["params"]["tool_version"].startswith("mlr 6.")
        assert doc["in_file_path"] == "sample_info.csv"


def test_z_score_and_centring_match_r_scale(page_workdir, tmp_path):
    workdir = page_workdir(PAGE)
    require("Rscript")
    script = tmp_path / "scale.R"
    script.write_text(
        "d <- read.csv(commandArgs(TRUE)[1], colClasses = c(sample = 'character'))\n"
        "out <- data.frame(sample = d$sample, z = scale(d$age)[, 1],\n"
        "                  c = scale(d$age, scale = FALSE)[, 1])\n"
        "write.csv(out, commandArgs(TRUE)[2], row.names = FALSE)\n"
    )
    r_out = tmp_path / "scale.csv"
    subprocess.run(
        ["Rscript", str(script), str(workdir / "sample_info.csv"), str(r_out)], check=True
    )
    r = read(r_out)
    z = read(workdir / "sample_info.age_zscore.csv")
    c = read(workdir / "sample_info.age_center.csv")
    assert list(r["sample"]) == SAMPLES
    np.testing.assert_allclose(z["age_zscore"].astype(float), r["z"].astype(float), rtol=1e-12)
    np.testing.assert_allclose(
        c["age_center"].astype(float), r["c"].astype(float), rtol=1e-12, atol=1e-12
    )


def _replace(column, values):
    """The good sheet with *column* set to *values* ({sample: text})."""
    rows = GOOD.splitlines()
    header = rows[0].split(",")
    j = header.index(column)
    out = [rows[0]]
    for row in rows[1:]:
        cells = row.split(",")
        cells[j] = values.get(cells[0], cells[j])
        out.append(",".join(cells))
    return "\n".join(out) + "\n"


ALL_AGE_40 = {s: "40" for s in SAMPLES}

# (derived column, source column, bad values, the samples the recipe names)
FAILURES = [
    *[
        (name, "conc", values, named)
        for name in ("conc_log2", "conc_log10", "conc_ln")
        for values, named in [
            ({"009": ""}, ["009"]),
            ({"011": "0"}, ["011"]),
            ({"010": "-3.5"}, ["010"]),
            ({"008": "NA"}, ["008"]),
            ({"009": "", "011": "0"}, ["009", "011"]),
        ]
    ],
    ("dose_log2_pc1", "dose", {"009": ""}, ["009"]),
    ("dose_log2_pc1", "dose", {"010": "-1"}, ["010"]),
    ("dose_log2_pc1", "dose", {"010": "-2", "012": "x"}, ["010", "012"]),
    ("age_zscore", "age", {"012": ""}, ["012"]),
    ("age_zscore", "age", ALL_AGE_40, SAMPLES),
    ("age_zscore", "age", {"007": "7.2", "008": "7.2", "009": "7.2", "010": "7.2",
                           "011": "7.2", "012": "7.2"}, SAMPLES),
    ("age_center", "age", {"007": "", "011": "NA"}, ["007", "011"]),
    ("age_minmax", "age", {"012": ""}, ["012"]),
    ("age_minmax", "age", ALL_AGE_40, SAMPLES),
]  # fmt: skip


@pytest.mark.parametrize(
    "name, column, values, named",
    FAILURES,
    ids=[f"{n}-{'+'.join(f'{k}={v!r}' for k, v in sorted(vals.items()))}" for n, _, vals, _ in FAILURES],
)  # fmt: skip
def test_recipe_fails_on_a_bad_value(tmp_path, name, column, values, named):
    """Each failure of DETK-0062 item 2: exit non-zero, the samples named on
    stderr, no output file and no module JSON."""
    require("mlr")
    (tmp_path / "sample_info.csv").write_text(_replace(column, values))
    p = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", recipes()[name]],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert p.returncode != 0, p.stdout + p.stderr
    lines = [x for x in p.stderr.splitlines() if x.startswith(f"{name}: ")]
    assert len(lines) == 1, p.stderr
    listed = re.findall(r"\b\d{3}\b", lines[0])
    assert listed == named, lines[0]
    assert "detk-util: error: command failed with exit status 1" in p.stderr
    assert not (tmp_path / f"sample_info.{name}.csv").exists()
    assert not list((tmp_path / "detk_report").glob("json/*.json"))


def test_centring_a_column_that_does_not_vary_is_not_an_error(tmp_path):
    require("mlr")
    (tmp_path / "sample_info.csv").write_text(_replace("age", ALL_AGE_40))
    subprocess.run(["bash", "-euo", "pipefail", "-c", recipes()["age_center"]], cwd=tmp_path,
                   check=True, capture_output=True)  # fmt: skip
    out = read(tmp_path / "sample_info.age_center.csv")
    assert (out["age_center"].astype(float) == 0).all()


def test_log2_pc1_takes_values_above_minus_one(tmp_path):
    require("mlr")
    (tmp_path / "sample_info.csv").write_text(_replace("dose", {"010": "-0.5"}))
    subprocess.run(["bash", "-euo", "pipefail", "-c", recipes()["dose_log2_pc1"]], cwd=tmp_path,
                   check=True, capture_output=True)  # fmt: skip
    out = read(tmp_path / "sample_info.dose_log2_pc1.csv")
    np.testing.assert_allclose(out["dose_log2_pc1"].astype(float),
                               np.log2(out["dose"].astype(float) + 1), rtol=1e-12)  # fmt: skip


# the skill -----------------------------------------------------------------


def _norm(text):
    return " ".join(text.split())


def test_every_recipe_in_the_skill_is_on_the_page():
    """The skill carries the page's recipes in short form: each of its bash
    blocks appears on the page as written (DETK-0062 item 1)."""
    page = _norm(PAGE.read_text())
    blocks = [b for b in parse(SKILL_REF).blocks if b.lang == "bash"]
    assert len(blocks) >= len(EXPECTED)
    for block in blocks:
        assert _norm(block.code) in page, f"{SKILL_REF.name}:{block.line} is not on {PAGE.name}"
    recorded = {re.search(r"-o (\S+)", b.code).group(1) for b in blocks if "record" in b.code}
    for name in EXPECTED:
        assert f"sample_info.{name}.csv" in recorded


def test_the_skill_points_to_the_recipes_and_warns_about_gather():
    skill = SKILL.read_text()
    ref = SKILL_REF.read_text()
    assert "references/covariates.md" in skill
    for text in (skill, ref):
        flat = _norm(text)
        assert "tidyr" in flat and "csvtk" in flat
        assert "`detk-util gather`" in flat
        assert "`reshape`" in flat
    assert PAGE_URL in ref


# the formula error -----------------------------------------------------------


def test_the_formula_error_for_a_call_points_to_the_recipes():
    from de_toolkit.formula import DesignMatrix, FormulaParseError

    data = pd.DataFrame({"cont": [0.1, 0.5, 0.9, 0.3]}, index=list("abcd"))
    with pytest.raises(FormulaParseError) as e:
        DesignMatrix("cont ~ log2(cont)", data)
    assert PAGE_URL in str(e.value)
    # the URL is where mkdocs puts the page
    assert PAGE.exists()
    assert PAGE_URL.endswith(PAGE.relative_to(DOCS).with_suffix("").as_posix() + "/")


def test_formulas_page_links_to_the_recipes():
    assert "recipes/covariates.md" in (DOCS / "formulas.md").read_text()
