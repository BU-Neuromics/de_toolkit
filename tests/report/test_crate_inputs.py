"""Every file a detk command reads or writes is in its crate action (#209, #45).

Each test runs one command as a user would, in a fresh working directory,
and reads the Process Run Crate it writes: every file the command read is in
the action's ``object`` and every file it wrote in its ``result``. In 1.0.0
these actions lacked the file the test names (annotate's mapping file,
gather's per-sample files, rlog's sample information file, a side output
such as norm deseq2 --size-factors' file, norm fpkm and tpm's lengths file).
"""

import json

import pandas
import pytest

from de_toolkit.crate import CRATE_FILENAME
from de_toolkit.common import DetkModule

COUNTS = "gene,s1,s2,s3,s4\ng1,10,20,30,40\ng2,100,150,120,90\ng3,5,7,9,11\ng4,60,40,80,50\n"
SAMPLE_INFO = "sample,group\ns1,A\ns2,A\ns3,B\ns4,B\n"
LENGTHS = "gene,length\ng1,1000\ng2,2000\ng3,4000\ng4,500\n"


@pytest.fixture
def work(tmp_path, monkeypatch):
    "A working directory holding counts.csv and sample_info.csv"
    monkeypatch.chdir(tmp_path)
    (tmp_path / "counts.csv").write_text(COUNTS)
    (tmp_path / "sample_info.csv").write_text(SAMPLE_INFO)
    return tmp_path


def run(main, argv, monkeypatch):
    "Run *main* on *argv*, the process's command line, as the console script does"
    monkeypatch.setattr("sys.argv", argv)
    main(argv)


def action_files(work):
    """(object, result) of the one crate action in the default report: the
    ids of the files it read and wrote"""
    crate = json.loads((work / "detk_report" / CRATE_FILENAME).read_text())
    graph = {e["@id"]: e for e in crate["@graph"]}
    (action,) = [e for e in graph.values() if e["@type"] == "CreateAction"]
    objects = {o["@id"] for o in action.get("object", []) if not o["@id"].startswith("#")}
    results = {o["@id"] for o in action.get("result", [])}
    for ref in objects | results:
        assert graph[ref]["@type"] == "File"
    return objects, results


# ---------------------------------------------------------------- detk-util


def test_annotate_records_the_mapping_file(work, monkeypatch):
    # #45: in 1.0.0 the mapping file was a parameter only, not a File input
    from de_toolkit.util import main

    (work / "de.csv").write_text(",log2FoldChange\nENSG01,1.5\nENSG02,-2.0\n")
    (work / "mapping.csv").write_text("gene_id,symbol\nENSG01,A1BG\nENSG02,A2M\n")
    run(
        main, ["detk-util", "annotate", "-o", "annotated.csv", "de.csv", "mapping.csv"], monkeypatch
    )

    objects, results = action_files(work)
    assert objects == {"../de.csv", "../mapping.csv"}
    assert results == {"../annotated.csv"}


def test_gather_records_every_per_sample_file(work, monkeypatch):
    # in 1.0.0 gather listed its files in params["files"] and its action had
    # no File input
    from de_toolkit.util import main

    for name, n in (("s1", 10), ("s2", 20)):
        (work / f"{name}.counts.txt").write_text(f"g1\t{n}\ng2\t{n + 1}\n__no_feature\t0\n")
    argv = ["detk-util", "gather", "--format=htseq", "-o", "counts_gathered.csv"]
    run(main, argv + ["s1.counts.txt", "s2.counts.txt"], monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../s1.counts.txt", "../s2.counts.txt"}
    assert results == {"../counts_gathered.csv"}
    (doc,) = [json.loads(p.read_text()) for p in (work / "detk_report" / "json").glob("*.json")]
    assert doc["in_file_path"] is None
    assert doc["in_file_paths"] == ["s1.counts.txt", "s2.counts.txt"]


# ------------------------------------------------ the sample information file


def test_filter_records_the_sample_information_file(work, monkeypatch):
    from de_toolkit.filter import main

    argv = ["detk-filter", "-o", "filtered.csv", "mean(group) > 1", "counts.csv"]
    run(main, argv + ["sample_info.csv"], monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv", "../sample_info.csv"}
    assert results == {"../filtered.csv"}


def test_stats_records_the_sample_information_file(work, monkeypatch):
    from de_toolkit.stats import main

    argv = ["detk-stats", "pca", "-o", "pca.csv", "counts.csv", "sample_info.csv"]
    run(main, argv, monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv", "../sample_info.csv"}
    assert results == {"../pca.csv"}


class RlogCounts(DetkModule):
    "Stands in for transform.RlogCounts (DESeq2, R) and writes its --rda file"

    def __init__(self, count_obj, blind=True, rda=None):
        self.count_obj = count_obj
        self["params"] = {"design": count_obj.design, "blind": blind, "rda": rda}
        if rda is not None:
            with open(rda, "wb") as f:
                f.write(b"RDS")

    @property
    def output(self):
        return self.count_obj.counts

    @property
    def properties(self):
        return {"num_length": len(self.count_obj.counts)}


def test_rlog_records_the_sample_information_file_and_rda(work, monkeypatch):
    # in 1.0.0 a non-blind rlog's action had the counts file only, and no
    # result for its --rda file
    import de_toolkit.transform as transform

    monkeypatch.setattr(transform, "RlogCounts", RlogCounts)
    argv = ["detk-transform", "rlog", "--blind=False", "--rda=rlog.rds", "-o", "rlog.csv"]
    run(transform.main, argv + ["counts.csv", "counts ~ group", "sample_info.csv"], monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv", "../sample_info.csv"}
    assert results == {"../rlog.csv", "../rlog.rds"}


class VstCounts(RlogCounts):
    "Stands in for transform.VstCounts (DESeq2, R) and writes its --rda file"

    def __init__(self, count_obj, rda=None):
        super().__init__(count_obj, rda=rda)


def test_vst_records_its_rda_file(work, monkeypatch):
    import de_toolkit.transform as transform

    monkeypatch.setattr(transform, "VstCounts", VstCounts)
    argv = ["detk-transform", "vst", "--rda=vst.rds", "-o", "vst.csv", "counts.csv"]
    run(transform.main, argv, monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv"}
    assert results == {"../vst.csv", "../vst.rds"}


# ------------------------------------------------------------- side outputs


def test_outlier_entropy_records_its_plot(work, monkeypatch):
    # detk-outlier reads no sample information file; its side output is the
    # --plot-output PNG, which 1.0.0 did not list
    pytest.importorskip("matplotlib")
    from de_toolkit.outlier import main

    argv = ["detk-outlier", "entropy", "-p", "0.5", "-o", "entropy.csv"]
    run(main, argv + ["--plot-output=entropy.png", "counts.csv"], monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv"}
    assert results == {"../entropy.csv", "../entropy.png"}


def test_norm_deseq2_records_its_size_factors_file(work, monkeypatch):
    from de_toolkit.norm import main

    argv = ["detk-norm", "deseq2", "--size-factors=sf.tsv", "-o", "norm.csv", "counts.csv"]
    run(main, argv, monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv"}
    assert results == {"../norm.csv", "../sf.tsv"}


def test_norm_deseq2_size_factors_with_counts_on_stdout(work, monkeypatch, capsys):
    # standard output is no file; the size factors file still is one
    from de_toolkit.norm import main

    run(main, ["detk-norm", "deseq2", "--size-factors=sf.tsv", "counts.csv"], monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv"}
    assert results == {"../sf.tsv"}


@pytest.mark.parametrize("cmd", ["fpkm", "tpm"])
def test_norm_records_the_lengths_file(work, monkeypatch, cmd):
    from de_toolkit.norm import main

    (work / "lengths.csv").write_text(LENGTHS)
    run(main, ["detk-norm", cmd, "-o", "norm.csv", "counts.csv", "lengths.csv"], monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv", "../lengths.csv"}
    assert results == {"../norm.csv"}


def test_the_module_json_keeps_the_primary_input(work, monkeypatch):
    # in_file_path stays the file the module processed; the others are in
    # in_file_paths beside it, as fgsea records them (DETK-0720)
    from de_toolkit.util import main

    (work / "de.csv").write_text(",log2FoldChange\nENSG01,1.5\n")
    (work / "mapping.csv").write_text("gene_id,symbol\nENSG01,A1BG\n")
    run(main, ["detk-util", "annotate", "-o", "a.csv", "de.csv", "mapping.csv"], monkeypatch)
    (doc,) = [json.loads(p.read_text()) for p in (work / "detk_report" / "json").glob("*.json")]
    assert doc["in_file_path"] == "de.csv"
    assert doc["in_file_paths"] == ["de.csv", "mapping.csv"]
    assert doc["params"]["mapping_fn"] == "mapping.csv"
    assert pandas.read_csv(work / "a.csv", index_col=0).loc["ENSG01", "symbol"] == "A1BG"


def test_outlier_entropy_plot_without_a_table(work, monkeypatch):
    # without -o entropy writes no table; its plot is its one output
    pytest.importorskip("matplotlib")
    from de_toolkit.outlier import main

    argv = ["detk-outlier", "entropy", "-p", "0.5", "--plot-output=entropy.png", "counts.csv"]
    run(main, argv, monkeypatch)

    objects, results = action_files(work)
    assert objects == {"../counts.csv"}
    assert results == {"../entropy.png"}
    (doc,) = [json.loads(p.read_text()) for p in (work / "detk_report" / "json").glob("*.json")]
    assert doc["out_file_path"] == "entropy.png"
    assert "out_file_paths" not in doc
