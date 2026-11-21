"""Checks of docs/tutorials/airway.md too deep to show on the page: detk's
DESeq2 results and size factors against DESeq2 run directly in R on the
page's own files."""

import subprocess

import numpy as np
import pandas as pd
import pytest

PAGE = "tutorials/airway.md"

# DESeq2 as its vignette runs it, on the page's filtered counts and sample
# information, with the page's design (cell line, then treatment with untrt
# as the reference). results() is asked for every gene's adjusted p-value
# (no independent filtering, no Cook's distance cutoff), which is what detk
# reports; with four samples a group DESeq() replaces no outliers.
DIRECT = r"""
suppressMessages(library(DESeq2))
args <- commandArgs(trailingOnly = TRUE)
counts <- read.csv("counts_filtered.csv", row.names = 1, check.names = FALSE)
info <- read.csv("sample_info.csv", row.names = 1, stringsAsFactors = TRUE)
info$dex <- relevel(info$dex, ref = "untrt")
stopifnot(identical(colnames(counts), rownames(info)))
dds <- DESeqDataSetFromMatrix(as.matrix(counts), info, design = ~ cell + dex)
dds <- DESeq(dds, quiet = TRUE)
res <- results(dds, name = "dex_trt_vs_untrt",
               independentFiltering = FALSE, cooksCutoff = FALSE)
write.csv(as.data.frame(res), args[1])
write.csv(data.frame(size_factor = sizeFactors(dds)), args[2])
"""


@pytest.fixture(scope="module")
def direct(tutorial_workdir, tmp_path_factory):
    workdir = tutorial_workdir(PAGE)
    out = tmp_path_factory.mktemp("airway_direct")
    results, size_factors = out / "results.csv", out / "size_factors.csv"
    subprocess.run(
        ["Rscript", "-e", DIRECT, str(results), str(size_factors)],
        cwd=workdir,
        check=True,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    return (
        workdir,
        pd.read_csv(results, index_col=0),
        pd.read_csv(size_factors, index_col=0)["size_factor"],
    )


def test_results_match_deseq2(direct):
    """detk-de deseq2's treatment columns are DESeq2's results() for the
    same design, gene for gene."""
    workdir, expected, _ = direct
    detk = pd.read_csv(workdir / "deseq2_results.csv", index_col=0)
    assert list(detk.index) == list(expected.index)
    np.testing.assert_allclose(detk["baseMean"], expected["baseMean"], rtol=1e-8)
    for stat in ("log2FoldChange", "lfcSE", "stat", "pvalue", "padj"):
        np.testing.assert_allclose(
            detk[f"dex__trt__{stat}"], expected[stat], rtol=1e-6, atol=1e-300, err_msg=stat
        )


def test_symbols_annotate_the_results(direct):
    """detk-util annotate adds the map's symbol to the results and changes
    nothing else."""
    workdir, _, _ = direct
    results = pd.read_csv(workdir / "deseq2_results.csv", index_col=0, dtype=str)
    annotated = pd.read_csv(workdir / "deseq2_results_symbols.csv", index_col=0, dtype=str)
    gene_map = pd.read_csv(workdir / "gene_map.csv", index_col=0, dtype=str)
    pd.testing.assert_frame_equal(annotated.drop(columns="symbol"), results)
    expected = gene_map["symbol"].reindex(results.index)
    pd.testing.assert_series_equal(annotated["symbol"], expected, check_names=False)


def test_size_factors_match_deseq2(direct):
    """detk-norm deseq2's size factors, computed in Python, are DESeq2's."""
    workdir, _, expected = direct
    detk = pd.read_csv(workdir / "size_factors.tsv", sep="\t", index_col=0)["size_factor"]
    assert list(detk.index) == list(expected.index)
    np.testing.assert_allclose(detk, expected, rtol=1e-10)


def test_report_has_every_step(tutorial_workdir):
    """The report the page makes, the one published as detk's example, has a
    section for every step that writes one."""
    workdir = tutorial_workdir(PAGE)
    html = (workdir / "detk_report" / "detk_report.html").read_text()
    for module in (
        "basestats",
        "pca",
        "filtercounts",
        "deseq2norm",
        "vstcounts",
        "entropycounts",
        "deseq2counts",
    ):
        assert module in html, f"{module} missing from the airway report"
    assert (workdir / "detk_report" / "ro-crate-metadata.json").exists()
