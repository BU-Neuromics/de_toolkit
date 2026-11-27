"""What identifies a module record (#182): runs that differ only in their
files keep separate records, and re-running an identical command replaces
its one record.

On v1.0.0 a record's id hashed the module name, its parameters, the primary
input and the detk version only, so two runs that differed only in an
output, a sample information file or a file the module does not record
(fgsea's results file) wrote the same ``json/<id>.json`` and the second
silently replaced the first."""

import json
import os
import subprocess
import sys

import pytest

from de_toolkit.crate import CRATE_FILENAME
from de_toolkit.report import DetkReport
from de_toolkit.wrapr import check_r_package

PY = sys.executable

COUNTS = "gene,s1,s2,s3,s4,s5,s6\n" + "".join(
    f"g{g},{10 + 7 * g},{14 + 5 * g},{12 + 6 * g},{40 + 3 * g * g % 97},"
    f"{35 + (g * 13) % 41},{44 + (g * 7) % 53}\n"
    for g in range(60)
)
SAMPLES = "sample,group\ns1,a\ns2,a\ns3,a\ns4,b\ns5,b\ns6,b\n"
# the same samples labelled otherwise: the kind of mismatched sheet the
# audit found collapsed into one record with the right one
SAMPLES_OTHER = "sample,group\ns1,a\ns2,b\ns3,a\ns4,b\ns5,a\ns6,b\n"

GMT = "".join(
    f"set{k}\tdescription\t" + "\t".join(f"g{g}" for g in range(k, 60, 4)) + "\n" for k in range(4)
)
RESULT = "gene,stat\n" + "".join(f"g{g},{(g * 37) % 60 - 30}.5\n" for g in range(60))
RESULT_OTHER = "gene,stat\n" + "".join(f"g{g},{30 - (g * 23) % 60}.25\n" for g in range(60))

deseq2_test = pytest.mark.skipif(
    not check_r_package("DESeq2"), reason="DESeq2 package not installed, skipping test"
)
fgsea_test = pytest.mark.skipif(
    not check_r_package("fgsea"), reason="fgsea package not installed, skipping test"
)


def run(args, cwd):
    "Run a detk console script in *cwd*, as a user would"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(PY) + os.pathsep + env.get("PATH", "")
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    assert p.returncode == 0, f"{args} failed\n{p.stdout}\n{p.stderr}"
    return p


@pytest.fixture
def work(tmp_path):
    w = tmp_path / "work"
    w.mkdir()
    (w / "counts.csv").write_text(COUNTS)
    (w / "samples.csv").write_text(SAMPLES)
    (w / "samples_other.csv").write_text(SAMPLES_OTHER)
    (w / "sets.gmt").write_text(GMT)
    (w / "result.csv").write_text(RESULT)
    (w / "result_other.csv").write_text(RESULT_OTHER)
    return w


def records(work):
    report = work / "detk_report"
    return [json.loads(p.read_text()) for p in sorted((report / "json").glob("*.json"))]


def crate_actions(work):
    "The crate's CreateActions, after detk-report generate"
    run(["detk-report", "generate"], work)
    graph = json.loads((work / "detk_report" / CRATE_FILENAME).read_text())["@graph"]
    return [e for e in graph if e["@type"] == "CreateAction"]


def inputs_and_outputs(action):
    "The files an action used and made, as named in the crate (rooted in detk_report/)"

    def files(key):
        return sorted(e["@id"] for e in action.get(key, []) if not e["@id"].startswith("#"))

    return files("object"), files("result")


# ------------------------------------------- the reproductions, end to end


def test_filter_runs_writing_different_outputs_keep_two_records(work):
    expr = "mean(all) > 10"
    run(["detk-filter", "-o", "a.csv", expr, "counts.csv"], work)
    run(["detk-filter", "-o", "b.csv", expr, "counts.csv"], work)

    docs = records(work)
    assert len(docs) == 2
    assert sorted(d["out_file_path"] for d in docs) == ["a.csv", "b.csv"]
    assert len({d["id"] for d in docs}) == 2

    acts = crate_actions(work)
    assert sorted(inputs_and_outputs(a) for a in acts) == [
        (["../counts.csv"], ["../a.csv"]),
        (["../counts.csv"], ["../b.csv"]),
    ]


@deseq2_test
def test_deseq2_runs_on_different_sample_sheets_keep_two_records(work):
    for sheet in ("samples_other.csv", "samples.csv"):
        run(
            ["detk-de", "deseq2", "-o", "de.csv", "counts ~ group", "counts.csv", sheet],
            work,
        )

    docs = records(work)
    assert len(docs) == 2
    assert sorted(d["column_data_path"] for d in docs) == ["samples.csv", "samples_other.csv"]

    acts = crate_actions(work)
    assert sorted(inputs_and_outputs(a) for a in acts) == [
        (["../counts.csv", "../samples.csv"], ["../de.csv"]),
        (["../counts.csv", "../samples_other.csv"], ["../de.csv"]),
    ]


@fgsea_test
def test_fgsea_runs_on_different_result_files_keep_two_records(work):
    for result in ("result.csv", "result_other.csv"):
        run(
            ["detk-enrich", "fgsea", "--minSize", "2", "-o", "gsea.csv", "sets.gmt", result],
            work,
        )

    docs = records(work)
    assert len(docs) == 2
    # fgsea records the results file as an input beside the GMT (DETK-0720)
    assert sorted(d["argv"][-1] for d in docs) == ["result.csv", "result_other.csv"]
    assert sorted(d["in_file_paths"][-1] for d in docs) == ["result.csv", "result_other.csv"]

    assert len(crate_actions(work)) == 2


# ---------------------------------------- an identical run replaces its one


def test_an_identical_filter_command_replaces_its_one_record(work):
    args = ["detk-filter", "-o", "a.csv", "mean(all) > 10", "counts.csv"]
    run(args, work)
    first = records(work)
    run(args, work)
    second = records(work)

    assert len(first) == len(second) == 1
    assert first[0]["id"] == second[0]["id"]
    # replaced, not kept: the second run's record is the one there
    assert second[0]["end_time"] >= first[0]["end_time"]
    assert len(crate_actions(work)) == 1


# ------------------------------------- every recorded path is in the id, no R


class _Module:
    "A stand-in for a DetkModule: what DetkModuleJSON reads of one"

    def __init__(self, name="deseq2", params=None):
        self.name = name
        self.params = params or {"design": "counts ~ group"}
        self.json = {"params": self.params, "properties": {}}


def _ids(tmp_path, calls, argv=None, monkeypatch=None):
    "Record each add_module(**kwargs) of *calls* in one report; their ids"
    if monkeypatch is not None and argv is not None:
        monkeypatch.setattr(sys, "argv", argv)
    report = DetkReport(str(tmp_path / "detk_report"))
    for kwargs in calls:
        report.add_module(_Module(), workdir=str(tmp_path), **kwargs)
    return [m.out_d["id"] for m in report.modules]


@pytest.mark.parametrize(
    "a,b",
    [
        ({"out_file_path": "a.csv"}, {"out_file_path": "b.csv"}),
        ({"column_data_path": "s1.csv"}, {"column_data_path": "s2.csv"}),
        ({"in_file_paths": ["x.csv", "s1.csv"]}, {"in_file_paths": ["x.csv", "s2.csv"]}),
        ({"out_file_paths": ["a.csv"]}, {"out_file_paths": ["b.csv"]}),
        ({"in_file_path": "x.csv"}, {"in_file_path": "y.csv"}),
    ],
)
def test_runs_differing_only_in_one_recorded_path_get_different_ids(tmp_path, a, b):
    base = {"in_file_path": "counts.csv", "out_file_path": "de.csv"}
    one, two = _ids(tmp_path, [{**base, **a}, {**base, **b}])
    assert one != two


def test_runs_differing_only_in_the_command_line_get_different_ids(tmp_path, monkeypatch):
    "a file the module does not record is in the command line (fgsea's results file in 1.0.0)"
    calls = [{"in_file_path": "sets.gmt", "out_file_path": "gsea.csv"}]
    (one,) = _ids(tmp_path, calls, ["detk-enrich", "fgsea", "sets.gmt", "r1.csv"], monkeypatch)
    (two,) = _ids(tmp_path, calls, ["detk-enrich", "fgsea", "sets.gmt", "r2.csv"], monkeypatch)
    assert one != two


def test_identical_runs_get_the_same_id(tmp_path, monkeypatch):
    calls = [{"in_file_path": "counts.csv", "column_data_path": "s.csv", "out_file_path": "o"}]
    argv = ["detk-de", "deseq2", "counts ~ group", "counts.csv", "s.csv", "-o", "o"]
    (one,) = _ids(tmp_path, calls, argv, monkeypatch)
    (two,) = _ids(tmp_path, calls, argv, monkeypatch)
    assert one == two


def test_an_absolute_path_and_its_relative_spelling_get_the_same_id(tmp_path, monkeypatch):
    "the id hashes the paths as recorded, relative to workdir (DETK-0280)"
    monkeypatch.setattr(sys, "argv", ["detk-filter"])
    (one,) = _ids(tmp_path, [{"in_file_path": "counts.csv", "out_file_path": "a.csv"}])
    (two,) = _ids(
        tmp_path,
        [{"in_file_path": str(tmp_path / "counts.csv"), "out_file_path": str(tmp_path / "a.csv")}],
    )
    assert one == two
