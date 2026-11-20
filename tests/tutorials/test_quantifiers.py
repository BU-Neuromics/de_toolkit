"""Checks of docs/tutorials/quantifiers.md too deep to show on the page."""

import subprocess
import sys

import numpy as np
import pandas as pd
from tutorial_runner import DOCS

PAGE = "tutorials/quantifiers.md"
DATA = DOCS / "tutorials" / "data" / "quantifiers"


def test_tpm_matches_direct_computation(tutorial_workdir):
    """The page's TPM is each count over its length in kilobases, scaled so
    each sample sums to a million, computed here from the page's own files."""
    workdir = tutorial_workdir(PAGE)
    counts = pd.read_csv(workdir / "counts_tidy.csv", index_col=0)
    lengths = pd.read_csv(workdir / "lengths.tsv", sep="\t", index_col=0).iloc[:, 0]
    tpm = pd.read_csv(workdir / "tpm.csv", index_col=0)

    rpk = counts.div(lengths.loc[counts.index] / 1e3, axis=0)
    expected = rpk / rpk.sum() * 1e6

    assert list(tpm.index) == list(counts.index)
    assert list(tpm.columns) == list(counts.columns)
    np.testing.assert_allclose(tpm.to_numpy(), expected.to_numpy(), rtol=1e-12)
    np.testing.assert_allclose(tpm.sum().to_numpy(), 1e6, rtol=1e-12)


def test_tpm_matches_salmon(tutorial_workdir):
    """The simulated samples share their effective lengths, so detk's TPM is
    salmon's own TPM column, as the page says, to the six decimals salmon
    writes."""
    workdir = tutorial_workdir(PAGE)
    tpm = pd.read_csv(workdir / "tpm.csv", index_col=0)
    for sample in tpm.columns:
        quant = pd.read_csv(DATA / "salmon" / sample / "quant.sf", sep="\t", index_col=0)
        np.testing.assert_allclose(tpm[sample], quant.loc[tpm.index, "TPM"], rtol=0, atol=5e-6)


def test_simulate_reproduces_the_data(tmp_path):
    """The committed data are what the seeded script writes, byte for byte."""
    subprocess.run([sys.executable, str(DATA / "simulate.py"), str(tmp_path)], check=True)
    written = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file())
    committed = sorted(
        p.relative_to(DATA)
        for p in DATA.rglob("*")
        if p.is_file() and p.name != "simulate.py" and "__pycache__" not in p.parts
    )
    assert written == committed
    for rel in written:
        assert (tmp_path / rel).read_bytes() == (DATA / rel).read_bytes(), rel
