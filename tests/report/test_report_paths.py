"""Where the Process Run Crate is written and what recorded paths are
relative to (DETK-0280): each report directory holds its own crate, rooted
there, and no recorded path names a directory of the machine."""

import json
import os
import subprocess
import sys

import pytest

from de_toolkit.crate import CRATE_FILENAME

PY = sys.executable

COUNTS = "gene,s1,s2,s3,s4\n" + "".join(
    f"g{g},{10 + g},{20 + 2 * g},{15 + g},{30 + 3 * g}\n" for g in range(30)
)
SAMPLES = "sample,group\ns1,a\ns2,a\ns3,b\ns4,b\n"


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
    return w


def docs(report):
    return [json.loads(p.read_text()) for p in sorted((report / "json").glob("*.json"))]


def crate(report):
    graph = json.loads((report / CRATE_FILENAME).read_text())["@graph"]
    return {e["@id"]: e for e in graph}


def actions(graph):
    return [e for e in graph.values() if e["@type"] == "CreateAction"]


def tool_names(graph):
    return sorted(graph[a["instrument"]["@id"]]["name"] for a in actions(graph))


# ---------------------------------------------------- one crate per report


def test_two_report_dirs_each_get_their_own_crate(work):
    run(["detk-stats", "summary", "--report-dir=a", "counts.csv"], work)
    run(["detk-filter", "--report-dir=b", "-o", "f.csv", "mean(all) > 20", "counts.csv"], work)

    assert not (work / CRATE_FILENAME).exists()
    a, b = crate(work / "a"), crate(work / "b")
    assert "detk-filter" not in tool_names(a)
    assert "detk-stats basestats" in tool_names(a)
    assert tool_names(b) == ["detk-filter"]
    # each is rooted in its own report directory
    (fa,) = actions(b)
    assert {o["@id"] for o in fa["object"] if not o["@id"].startswith("#")} == {"../counts.csv"}
    assert [r["@id"] for r in fa["result"]] == ["../f.csv"]
    assert a["ro-crate-metadata.json"]["about"] == {"@id": "./"}


def test_generate_writes_the_crate_into_the_report_dir(work):
    run(["detk-stats", "summary", "--no-report", "counts.csv"], work)
    run(["detk-stats", "summary", "counts.csv"], work)
    os.remove(work / "detk_report" / CRATE_FILENAME)
    run(["detk-report", "generate"], work)
    assert (work / "detk_report" / CRATE_FILENAME).exists()
    assert not (work / CRATE_FILENAME).exists()


def test_clean_removes_the_crate_with_the_report_and_leaves_an_old_one(work):
    # a ./ro-crate-metadata.json an earlier detk version wrote
    old = work / CRATE_FILENAME
    old.write_text('{"@graph": []}\n')
    run(["detk-stats", "summary", "counts.csv"], work)
    assert (work / "detk_report" / CRATE_FILENAME).exists()
    run(["detk-report", "clean"], work)
    assert not (work / "detk_report").exists()
    assert old.read_text() == '{"@graph": []}\n'


# --------------------------------------------------- the recorded paths


def test_default_report_dir_records_workdir_dotdot(work):
    run(["detk-stats", "summary", "-o", "s.csv", "counts.csv", "samples.csv"], work)
    for doc in docs(work / "detk_report"):
        assert doc["workdir"] == ".."
        assert doc["argv"][0] == "detk-stats"
        assert doc["in_file_path"] == "counts.csv"
        assert doc["column_data_path"] == "samples.csv"


def test_absolute_typed_paths_are_written_relative(work):
    (work / "out").mkdir()
    run(
        [
            "detk-filter",
            f"--report-dir={work / 'rep'}",
            "-o",
            str(work / "out" / "f.csv"),
            "mean(all) > 20",
            str(work / "counts.csv"),
        ],
        work,
    )
    (doc,) = docs(work / "rep")
    assert doc["workdir"] == ".."
    assert doc["in_file_path"] == "counts.csv"
    assert doc["out_file_path"] == "out/f.csv"
    (action,) = actions(crate(work / "rep"))
    assert [r["@id"] for r in action["result"]] == ["../out/f.csv"]


def _machine_paths(work):
    "The absolute directories of this machine that no report may hold"
    paths = {str(work), os.path.realpath(work), PY, os.path.dirname(PY), sys.prefix}
    home = os.path.expanduser("~")
    if home not in ("/", ""):
        paths.add(home)
    return {p for p in paths if p}


def _assert_no_machine_paths(text, where, work):
    for p in _machine_paths(work):
        assert p not in text, f"{where} holds {p}"
    assert "file://" not in text, f"{where} holds a file:// URI"


@pytest.mark.parametrize("inside", [True, False], ids=["report-inside", "report-outside"])
def test_no_machine_path_in_module_json_report_or_crate(work, tmp_path, inside):
    report = work / "rep" if inside else tmp_path / "elsewhere" / "rep"
    rd = "rep" if inside else "../elsewhere/rep"
    run(["detk-stats", "summary", f"--report-dir={rd}", "counts.csv", "samples.csv"], work)
    run(
        ["detk-filter", f"--report-dir={rd}", "-o", "f.csv", "mean(all) > 20", "counts.csv"],
        work,
    )
    run(
        [
            "detk-util",
            "record",
            f"--report-dir={rd}",
            "-i",
            "samples.csv",
            "-o",
            "copy.csv",
            "--tool",
            "cp",
            "--tool-version",
            "1",
            "--",
            "cp",
            "samples.csv",
            "copy.csv",
        ],
        work,
    )

    expected_workdir = ".." if inside else "../../work"
    for path in sorted((report / "json").glob("*.json")):
        text = path.read_text()
        _assert_no_machine_paths(text, path.name, work)
        doc = json.loads(text)
        assert doc["workdir"] == expected_workdir
        assert not os.path.isabs(doc["argv"][0])
        # the recorded paths resolve, from the report directory, to the files
        for key in ("in_file_path", "out_file_path", "column_data_path"):
            if doc.get(key) not in (None, "stdout", "-"):
                assert (report / doc["workdir"] / doc[key]).exists(), (key, doc[key])

    html = (report / "detk_report.html").read_text()
    start = html.index('id="detk-raw">') + len('id="detk-raw">')
    payload = html[start : html.index("</script>", start)]
    _assert_no_machine_paths(payload, "the report's embedded payload", work)
    assert expected_workdir in payload

    crate_text = (report / CRATE_FILENAME).read_text()
    _assert_no_machine_paths(crate_text, "the crate", work)
    graph = crate(report)
    files = [e["@id"] for e in graph.values() if e["@type"] == "File"]
    assert files
    for ref in files:
        assert not os.path.isabs(ref)
        if os.path.basename(ref) != "stdout":
            assert (report / ref).exists(), ref
