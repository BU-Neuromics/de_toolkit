"""Checks of docs/tutorials/covariates.md too deep to show on the page: the
derived columns against numpy, and the records the page's steps left."""

import json

import numpy as np
import pandas as pd

PAGE = "tutorials/covariates.md"


def test_derived_columns(tutorial_workdir):
    """The Miller recipes' columns are the z-score (sd over n - 1) and log2
    of avgLength, and the constant; the sheet's own columns are unchanged."""
    workdir = tutorial_workdir(PAGE)
    source = pd.read_csv(workdir / "sample_info.csv", dtype=str)
    derived = pd.read_csv(workdir / "sample_info.covariates.csv", dtype=str)
    pd.testing.assert_frame_equal(derived[source.columns], source)
    x = source["avgLength"].astype(float)
    np.testing.assert_allclose(
        derived["avgLength_zscore"].astype(float), (x - x.mean()) / x.std(ddof=1), rtol=1e-12
    )
    np.testing.assert_allclose(derived["avgLength_log2"].astype(float), np.log2(x), rtol=1e-12)
    assert set(derived["study"]) == {"airway"}


def test_design_used_the_derived_column(tutorial_workdir):
    """detk-de deseq2 fitted a coefficient for the z-scored read length."""
    workdir = tutorial_workdir(PAGE)
    results = pd.read_csv(workdir / "deseq2_results.csv", index_col=0)
    assert results["avgLength_zscore__pvalue"].notna().any()
    assert results["dex__trt__pvalue"].notna().any()


def test_records(tutorial_workdir):
    """Each successful detk-util record left a record (R once, Miller three
    times); the failing recipe left none and no output file."""
    workdir = tutorial_workdir(PAGE)
    docs = [json.loads(p.read_text()) for p in (workdir / "detk_report" / "json").glob("*.json")]
    records = [d for d in docs if d.get("name") == "record"]
    tools = sorted(d["params"]["tool"] for d in records)
    assert tools == ["Rscript", "mlr", "mlr", "mlr"]
    outputs = {p for d in records for p in d["out_file_paths"]}
    assert not any("bad" in p for p in outputs)
    assert not (workdir / "sample_info_bad.log2.csv").exists()
