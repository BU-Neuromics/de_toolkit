"""Where the Process Run Crate is written and what recorded paths are
relative to (DETK-0280): each report directory holds its own crate, rooted
there, and no recorded path names a directory of the machine."""

import json
import os
import shlex
import shutil
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


# ------------------------------------------- absolute paths typed (DETK-0281)


def _report_text(report):
    "every module JSON, the report's embedded payload and the crate, as text"
    texts = {p.name: p.read_text() for p in sorted((report / "json").glob("*.json"))}
    html = (report / "detk_report.html").read_text()
    start = html.index('id="detk-raw">') + len('id="detk-raw">')
    texts["the report's embedded payload"] = html[start : html.index("</script>", start)]
    texts["the crate"] = (report / CRATE_FILENAME).read_text()
    return texts


def _no_absolute_arg(argv):
    for arg in argv:
        value = arg.split("=", 1)[1] if arg.startswith("--") and "=" in arg else arg
        assert not os.path.isabs(value), arg


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
    run(
        ["detk-stats", "summary", "--report-dir", str(work / "rep"), str(work / "counts.csv")],
        work,
    )
    for where, text in _report_text(work / "rep").items():
        _assert_no_machine_paths(text, where, work)
    for doc in docs(work / "rep"):
        assert doc["workdir"] == ".."
        assert doc["in_file_path"] == "counts.csv"
        _no_absolute_arg(doc["argv"])
        if doc["name"] == "filtercounts":
            assert doc["out_file_path"] == "out/f.csv"
            assert doc["argv"][1:] == [
                "--report-dir=rep",
                "-o",
                "out/f.csv",
                "mean(all) > 20",
                "counts.csv",
            ]
        else:
            assert doc["argv"][1:] == ["summary", "--report-dir", "rep", "counts.csv"]
    filters = [a for a in actions(crate(work / "rep")) if a["name"] == "detk-filter run"]
    assert [r["@id"] for r in filters[0]["result"]] == ["../out/f.csv"]


def test_record_with_absolute_paths_records_them_relative(work):
    # the command typed by its absolute path too; a system one, since a
    # command in another tree is written as a ../ chain naming that tree's
    # directories (the residual DETK-0281 notes)
    cp = shutil.which("cp")
    if cp is None:
        pytest.skip("cp is not on PATH")
    run(
        [
            "detk-util",
            "record",
            f"--report-dir={work / 'rep'}",
            "-i",
            str(work / "samples.csv"),
            f"-o{work / 'copy.csv'}",
            "--tool",
            "cp",
            "--tool-version",
            "1",
            "--",
            cp,
            str(work / "samples.csv"),
            str(work / "copy.csv"),
        ],
        work,
    )
    assert (work / "copy.csv").read_text() == SAMPLES
    for where, text in _report_text(work / "rep").items():
        _assert_no_machine_paths(text, where, work)

    (doc,) = docs(work / "rep")
    _no_absolute_arg(doc["argv"])
    assert "--report-dir=rep" in doc["argv"] and "-ocopy.csv" in doc["argv"]
    params, props = doc["params"], doc["properties"]
    assert params["inputs"] == ["samples.csv"] and params["outputs"] == ["copy.csv"]
    assert params["argv"][1:] == ["samples.csv", "copy.csv"]
    assert not os.path.isabs(params["argv"][0])
    # the command, rebuilt from the recorded arguments, re-runs from workdir
    assert shlex.split(params["command"]) == params["argv"]
    assert [d["path"] for d in props["inputs"]] == ["samples.csv"]
    assert [d["path"] for d in props["outputs"]] == ["copy.csv"]
    # the checksums still reach the crate's File entities
    graph = crate(work / "rep")
    assert graph["../copy.csv"]["sha256"] == props["outputs"][0]["sha256"]
    assert graph["../samples.csv"]["sha256"] == props["inputs"][0]["sha256"]


@pytest.mark.parametrize(
    "arg,expected",
    [
        ("{w}/counts.csv", "counts.csv"),
        ("{w}/sub/c.csv", "sub/c.csv"),
        ("--report-dir={w}/rep", "--report-dir=rep"),
        ("-o{w}/out.csv", "-oout.csv"),
        ("{w}/../other/c.csv", "../other/c.csv"),
        ("counts.csv", "counts.csv"),
        ("mean(all) > 20", "mean(all) > 20"),
        ("counts ~ group", "counts ~ group"),
        ("--log", "--log"),
        ("-2.5", "-2.5"),
        ("-", "-"),
        ("--opt=value", "--opt=value"),
        # DETK-0580: an argument that starts with / but is not a path is kept
        ("/^gene/ {print}", "/^gene/ {print}"),
        ("/^g1,/", "/^g1,/"),
        ("/usr/bin/env echo hi", "/usr/bin/env echo hi"),
        ("--expr=/^g1,/", "--expr=/^g1,/"),
        ("-e/^g1,/", "-e/^g1,/"),
        # a path not yet written, in a directory that exists, is still a path
        ("{w}/not_yet.csv", "not_yet.csv"),
        ("{w}/no_such_dir/c.csv", "{w}/no_such_dir/c.csv"),
        # DETK-0590: an existing path is a path, whitespace or not
        ("{w}/My Data/c.csv", "My Data/c.csv"),
        ("{w}/My Data", "My Data"),
        ("--in={w}/My Data/c.csv", "--in=My Data/c.csv"),
        ("-i{w}/My Data/c.csv", "-iMy Data/c.csv"),
        # one that does not exist keeps DETK-0580's rule
        ("{w}/My Data/not_yet.csv", "{w}/My Data/not_yet.csv"),
    ],
)
def test_relative_arg(tmp_path, arg, expected):
    from de_toolkit.report import relative_arg

    # the directories the paths name exist, as they would for a real command
    w = os.path.realpath(tmp_path / "w")
    os.makedirs(os.path.join(w, "sub"))
    os.makedirs(os.path.join(w, "My Data"))
    open(os.path.join(w, "My Data", "c.csv"), "w").close()
    os.makedirs(os.path.join(tmp_path, "other"))
    assert relative_arg(arg.replace("{w}", w), w) == expected.replace("{w}", w)


@pytest.mark.parametrize(
    "command",
    [
        # an awk program and a regular expression that start with /, and a
        # shell script whose first word is an absolute program (DETK-0580)
        ["awk", "/^gene/ {print}", "{w}/counts.csv"],
        ["grep", "-v", "/^g1,/", "{w}/counts.csv"],
        ["sh", "-c", "/usr/bin/env echo hi"],
    ],
    ids=["awk", "grep", "sh-c"],
)
def test_record_keeps_arguments_that_only_start_with_a_slash(work, command):
    # the step writes copy.csv; its own arguments are recorded as typed but
    # for the absolute path of a real file, which is still made relative
    tool = shutil.which(command[0])
    if tool is None:
        pytest.skip(f"{command[0]} is not on PATH")
    argv = [a.replace("{w}", str(work)) for a in command]
    script = shlex.join(argv) + " > copy.csv || true; test -e copy.csv || : > copy.csv"
    run(
        [
            "detk-util", "record", "--tool", command[0], "--tool-version", "1",
            "-o", "copy.csv", "--", "sh", "-c", script,
        ],
        work,
    )  # fmt: skip
    (doc,) = docs(work / "detk_report")
    assert doc["params"]["argv"] == ["sh", "-c", script]

    # and given to record directly, as separate words
    (work / "detk_report").rename(work / "first_report")
    run(
        [
            "detk-util", "record", "--tool", command[0], "--tool-version", "1",
            "-i", "counts.csv", "-o", "counts.csv", "--", *argv,
        ],
        work,
    )  # fmt: skip
    (doc,) = docs(work / "detk_report")
    expected = ["counts.csv" if a == str(work / "counts.csv") else a for a in argv]
    assert doc["params"]["argv"] == expected
    assert shlex.split(doc["params"]["command"]) == expected
    # the argument starting with / is kept, word for word
    kept = [a for a in argv if a.startswith("/") and a != str(work / "counts.csv")]
    assert kept and all(a in doc["params"]["argv"] for a in kept)
    assert all(a in doc["argv"] for a in kept)


def test_record_writes_an_existing_path_with_spaces_relative(work):
    # DETK-0590: an existing absolute path with whitespace is a path, so
    # the recorded command line names it relative to workdir and re-runs
    cp = shutil.which("cp")
    if cp is None:
        pytest.skip("cp is not on PATH")
    (work / "My Data").mkdir()
    (work / "My Data" / "c.csv").write_text(SAMPLES)
    src = str(work / "My Data" / "c.csv")
    run(["detk-util", "record", "-i", src, "-o", "g.csv", "--", "cp", src, "g.csv"], work)
    assert (work / "g.csv").read_text() == SAMPLES

    (doc,) = docs(work / "detk_report")
    params = doc["params"]
    assert params["argv"] == ["cp", "My Data/c.csv", "g.csv"]
    assert params["inputs"] == ["My Data/c.csv"]
    assert "My Data/c.csv" in doc["argv"] and src not in doc["argv"]
    _no_absolute_arg(doc["argv"])
    for where, text in _report_text(work / "detk_report").items():
        _assert_no_machine_paths(text, where, work)
    # the recorded command re-runs from workdir
    (work / "g.csv").unlink()
    subprocess.run(shlex.split(params["command"]), cwd=work, check=True)
    assert (work / "g.csv").read_text() == SAMPLES
