"""
detk-util record (DETK-0051 Option C, DETK-0061): run an external command
and record it as a step, in the module JSON and the Process Run Crate.

The external command is always a Python one-liner run with this interpreter,
so the tests need no Miller. Command lines run as the console script in a
subprocess, as a user would, so stdio, exit codes and the files written are
the real ones.
"""

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from importlib.resources import files as pkg_files

import pytest

from de_toolkit import util
from de_toolkit.crate import WFRUN_CONTEXT, build_crate
from de_toolkit.report import MODULE_SCHEMA_VERSION, DetkReport
from r_packages import needs_r

PY = sys.executable
TOOL = os.path.basename(PY)

# derive a column age_group from sample_info.csv's age into covs.csv
DERIVE = (
    "import csv;"
    "r=list(csv.reader(open('sample_info.csv')));"
    "r[0].append('age_group');"
    "[x.append('old' if int(x[2]) >= 50 else 'young') for x in r[1:]];"
    "csv.writer(open('covs.csv','w',newline='')).writerows(r)"
)

SAMPLE_INFO = "sample,group,age\ns1,a,31\ns2,a,55\ns3,a,52\ns4,b,38\ns5,b,61\ns6,b,47\n"


def _counts_csv():
    x = 12345
    samples = ["s1", "s2", "s3", "s4", "s5", "s6"]
    rows = ["gene," + ",".join(samples)]
    for g in range(200):
        base = 5 + (g * 37) % 500
        vals = []
        for j in range(len(samples)):
            x = (1103515245 * x + 12345) % 2**31
            effect = 3 if (g % 10 == 0 and j >= 3) else 1
            vals.append(str(int(base * effect * (0.6 + 0.8 * x / 2**31))))
        rows.append(f"g{g}," + ",".join(vals))
    return "\n".join(rows) + "\n"


def run(args, cwd, **kw):
    "Run a detk console script in *cwd*; the CompletedProcess"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(PY) + os.pathsep + env.get("PATH", "")
    kw.setdefault("capture_output", True)
    return subprocess.run(args, cwd=cwd, env=env, text=True, **kw)


def record(cwd, *args, command=None, **kw):
    "detk-util record ARGS -- COMMAND (default: the DERIVE one-liner)"
    command = [PY, "-c", DERIVE] if command is None else command
    return run(["detk-util", "record", *args, "--", *command], cwd, **kw)


def module_docs(cwd):
    json_dir = cwd / "detk_report" / "json"
    return [json.loads(p.read_text()) for p in sorted(json_dir.glob("*.json"))]


def crate_graph(cwd):
    "the crate and its graph; it is in the report directory (DETK-0280)"
    crate = json.loads((cwd / "detk_report" / "ro-crate-metadata.json").read_text())
    return crate, {e["@id"]: e for e in crate["@graph"]}


def _recorded(path, work):
    "an absolute *path* as module JSON records it: relative to workdir (DETK-0281)"
    real = os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))
    return os.path.relpath(real, os.path.realpath(work)).replace(os.sep, "/")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def work(tmp_path):
    (tmp_path / "sample_info.csv").write_text(SAMPLE_INFO)
    (tmp_path / "counts.csv").write_text(_counts_csv())
    return tmp_path


def schema():
    return json.loads(pkg_files("de_toolkit").joinpath("module_schema.json").read_text())


# ------------------------------------------------------------- module JSON


def test_records_the_step_in_the_module_json(work):
    p = record(work, "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    assert p.stdout == ""
    assert "age_group" in (work / "covs.csv").read_text()

    (doc,) = module_docs(work)
    assert doc["name"] == "record"
    assert doc["schema_version"] == MODULE_SCHEMA_VERSION == "1.2"
    assert doc["in_file_path"] == "sample_info.csv"
    assert doc["out_file_path"] == "covs.csv"
    assert doc["column_data_path"] is None
    assert doc["in_file_paths"] == ["sample_info.csv"]
    assert doc["out_file_paths"] == ["covs.csv"]

    params = doc["params"]
    # the interpreter, typed absolute, is found on PATH (run() puts its
    # directory first) by its name, so it is recorded by name (DETK-0390)
    assert params["argv"] == [TOOL, "-c", DERIVE]
    assert shlex.split(params["command"]) == params["argv"]
    assert params["tool"] == TOOL
    # the first line of 'python --version'
    assert params["tool_version"] == f"Python {sys.version.split()[0]}"
    assert params["inputs"] == ["sample_info.csv"]
    assert params["outputs"] == ["covs.csv"]

    props = doc["properties"]
    assert props["exit_status"] == 0
    assert props["inputs"] == [
        {
            "path": "sample_info.csv",
            "sha256": sha256(work / "sample_info.csv"),
            "size": (work / "sample_info.csv").stat().st_size,
        }
    ]
    assert props["outputs"] == [
        {
            "path": "covs.csv",
            "sha256": sha256(work / "covs.csv"),
            "size": (work / "covs.csv").stat().st_size,
        }
    ]


def test_module_json_validates_against_the_schema(work):
    jsonschema = pytest.importorskip("jsonschema")
    p = record(work, "-i", "sample_info.csv", "-i", "counts.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(work)
    jsonschema.validate(doc, schema())


def test_schema_takes_the_new_fields_as_optional_lists():
    jsonschema = pytest.importorskip("jsonschema")
    s = schema()
    assert "in_file_paths" not in s["required"] and "out_file_paths" not in s["required"]
    doc = {
        "name": "record",
        "id": "x",
        "schema_version": "1.1",
        "detk_version": "1",
        "last_modified": 0,
        "params": {},
        "properties": {},
        "in_file_paths": ["a.csv"],
        "out_file_paths": ["b.csv", "c.csv"],
    }
    jsonschema.validate(doc, s)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc | {"out_file_paths": "b.csv"}, s)


REPO = os.path.join(os.path.dirname(__file__), "..", "..")


def _fixture_documents():
    """Every module JSON document the repository holds: the documentation
    example report's embedded documents (schema 1.0, written by detk 0.9.12)
    and the shape the crate tests build"""
    docs = []
    with open(os.path.join(REPO, "docs", "example", "detk_report.html"), encoding="utf-8") as f:
        text = f.read()
    start = text.index('id="detk-raw">') + len('id="detk-raw">')
    docs += list(json.loads(text[start : text.index("</script>", start)]).values())
    docs.append(
        {
            "name": "deseq2norm",
            "id": "n1",
            "schema_version": "1.0",
            "detk_version": "0.9.12",
            "last_modified": 0,
            "start_time": "2026-08-11T15:00:00+00:00",
            "end_time": "2026-08-11T15:00:05+00:00",
            "params": {},
            "properties": {},
            "in_file_path": "a.csv",
            "out_file_path": None,
            "column_data_path": None,
            "workdir": None,
        }
    )
    return docs


def test_every_fixture_document_still_validates():
    jsonschema = pytest.importorskip("jsonschema")
    docs = _fixture_documents()
    assert len(docs) > 5
    s = schema()
    for doc in docs:
        jsonschema.validate(doc, s)


def test_other_modules_write_no_file_lists(tmp_path):
    # a document of a module with one input stays as before 1.1
    from de_toolkit.report import DetkModuleJSON

    class Fake(util.DetkModule):
        pass

    m = Fake()
    m["params"] = {}
    out = DetkModuleJSON(m, in_file_path="a.csv", json_dir=str(tmp_path)).out_d
    assert "in_file_paths" not in out and "out_file_paths" not in out


def test_several_inputs_and_outputs(work):
    both = "import shutil;shutil.copy('sample_info.csv','x.csv');shutil.copy('counts.csv','y.csv')"
    p = record(
        work,
        *("-i", "sample_info.csv", "-i", "counts.csv", "-o", "x.csv", "-o", "y.csv"),
        command=[PY, "-c", both],
    )
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(work)
    assert doc["in_file_paths"] == ["sample_info.csv", "counts.csv"]
    assert doc["out_file_paths"] == ["x.csv", "y.csv"]
    assert [d["path"] for d in doc["properties"]["outputs"]] == ["x.csv", "y.csv"]
    assert doc["properties"]["outputs"][1]["sha256"] == sha256(work / "counts.csv")


def test_no_inputs(work):
    p = record(work, "-o", "z.csv", command=[PY, "-c", "open('z.csv','w').write('a\\n')"])
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(work)
    assert doc["in_file_path"] is None
    assert doc["in_file_paths"] == []
    assert doc["properties"]["inputs"] == []


def test_no_report_writes_no_module_json(work):
    p = record(work, "--no-report", "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    assert (work / "covs.csv").exists()
    assert not (work / "detk_report").exists()
    assert not (work / "ro-crate-metadata.json").exists()


# ---------------------------------------------------------------- refusals


def _refused(p, work, *names):
    assert p.returncode == 1, (p.returncode, p.stderr)
    last = p.stderr.strip().splitlines()[-1]
    assert last.startswith("detk-util: error: "), last
    for name in names:
        assert name in last, f"{name!r} not in {last!r}"
    assert "Traceback" not in p.stderr
    assert not (work / "detk_report").exists(), "a refused record wrote module JSON"


def test_missing_input_exits_1_and_does_not_run(work):
    marker = "open('ran','w')"
    p = record(work, "-i", "nope.csv", "-o", "covs.csv", command=[PY, "-c", marker])
    _refused(p, work, "nope.csv")
    assert not (work / "ran").exists()


def test_missing_output_exits_1(work):
    p = record(work, "-i", "sample_info.csv", "-o", "covs.csv", "-o", "never.csv")
    _refused(p, work, "never.csv")
    # what the command wrote is left as it is
    assert (work / "covs.csv").exists()


def test_failed_command_exits_1_not_its_status(work):
    p = record(work, "-o", "covs.csv", command=[PY, "-c", "import sys; sys.exit(3)"])
    _refused(p, work, "exit status 3", TOOL)


def test_failed_command_that_wrote_its_output_records_nothing(work):
    code = "open('covs.csv','w').write('x'); import sys; sys.exit(2)"
    p = record(work, "-o", "covs.csv", command=[PY, "-c", code])
    _refused(p, work, "exit status 2")
    assert (work / "covs.csv").read_text() == "x"


# a program on several lines, as the Miller recipes pass theirs
MULTILINE = "\nimport sys\nsys.exit(3)\n"


def test_failed_multiline_command_is_shown_on_one_line(work):
    p = record(work, "-o", "covs.csv", command=[PY, "-c", MULTILINE, "it's"])
    _refused(p, work)
    last = p.stderr.strip().splitlines()[-1]
    assert last == (
        "detk-util: error: command failed with exit status 3: "
        f"{shlex.quote(PY)} -c '...' 'it'\"'\"'s' (--verbose for the traceback)"
    )


def test_multiline_argument_shows_its_first_line(work):
    code = "import sys  # first\nsys.exit(4)"
    p = record(work, "-o", "covs.csv", command=[PY, "-c", code])
    last = p.stderr.strip().splitlines()[-1]
    assert last.endswith(" -c 'import sys  # first...' (--verbose for the traceback)"), last


def test_killed_multiline_command_is_shown_on_one_line(work):
    code = "\nimport os, signal\nos.kill(os.getpid(), signal.SIGTERM)\n"
    p = record(work, "-o", "covs.csv", command=[PY, "-c", code])
    _refused(p, work, f"killed by signal {int(__import__('signal').SIGTERM)}")
    assert p.stderr.strip().splitlines()[-1].endswith(" -c '...' (--verbose for the traceback)")


def test_output_not_written_by_multiline_command_is_shown_on_one_line(work):
    p = record(work, "-o", "covs.csv", command=[PY, "-c", "\npass\n"])
    _refused(p, work, "covs.csv", "was not written")
    assert p.stderr.strip().splitlines()[-1].endswith(" -c '...' (--verbose for the traceback)")


@pytest.mark.parametrize(
    "argv, line",
    [
        (["mlr", "put", "$x = 1"], "mlr put '$x = 1'"),
        (["mlr", "put", "\n  @a = 1;\n  end {}\n"], "mlr put '...'"),
        (["awk", "BEGIN {\n print 1\n}"], "awk 'BEGIN {...'"),
        (["sh", "-c", "echo a\necho b"], "sh -c 'echo a...'"),
        (["sh", "-c", "it's\nx"], "sh -c 'it'\"'\"'s...'"),
    ],
)
def test_command_line(argv, line):
    assert util._command_line(argv) == line
    assert "\n" not in util._command_line(argv)


def test_command_not_found_exits_1(work):
    p = record(work, "-o", "covs.csv", command=["detk-no-such-command", "x"])
    _refused(p, work, "command not found", "detk-no-such-command")


def test_command_that_is_not_executable_exits_1(work):
    (work / "plain.txt").write_text("not a program\n")
    p = record(work, "-o", "covs.csv", command=["./plain.txt"])
    _refused(p, work, "./plain.txt")


def test_usage_errors_exit_2(work):
    for args in (
        ["detk-util", "record", "-o", "covs.csv"],
        ["detk-util", "record", "-o", "covs.csv", "--"],
        ["detk-util", "record", "--", PY, "-c", "pass"],
        ["detk-util", "record", "-o", "covs.csv", PY, "--", "x"],
    ):
        p = run(args, work)
        assert p.returncode == 2, (args, p.stderr)
        assert "usage: detk-util record" in p.stderr
        assert not (work / "detk_report").exists()


# ------------------------------------------------------------------- stdio


def test_stdio_is_the_commands(work):
    # stdout redirected to the output, as a shell redirect of the line does;
    # record writes nothing there itself, and its messages go to stderr
    code = "import sys; sys.stdout.write(sys.stdin.read().upper())"
    with open(work / "up.csv", "w") as out:
        p = record(
            work,
            "-o",
            "up.csv",
            command=[PY, "-c", code],
            input="a,b\n",
            capture_output=False,
            stdout=out,
            stderr=subprocess.PIPE,
        )
    assert p.returncode == 0, p.stderr
    assert (work / "up.csv").read_text() == "A,B\n"
    assert "detk version" in p.stderr  # the log, on stderr
    (doc,) = module_docs(work)
    assert doc["properties"]["outputs"][0]["sha256"] == sha256(work / "up.csv")


def test_command_runs_without_a_shell(work):
    # a shell would expand $HOME and the redirect; without one they are
    # arguments the command sees as given
    code = "import sys; open('args.txt','w').write(repr(sys.argv[1:]))"
    p = record(work, "-o", "args.txt", command=[PY, "-c", code, "$HOME", ">", "x"])
    assert p.returncode == 0, p.stderr
    assert (work / "args.txt").read_text() == repr(["$HOME", ">", "x"])
    assert not (work / "x").exists()


def test_through_the_umbrella(work):
    p = run(
        [
            "detk",
            "util",
            "record",
            "-i",
            "sample_info.csv",
            "-o",
            "covs.csv",
            "--",
            PY,
            "-c",
            DERIVE,
        ],
        work,
    )
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(work)
    assert doc["name"] == "record"


# ------------------------------------------------------------ tool version


def test_tool_version_given_is_recorded(work):
    p = record(work, "--tool-version=9.9", "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(work)
    assert doc["params"]["tool_version"] == "9.9"
    assert "not known" not in p.stderr


def test_another_tool_is_unknown_with_a_warning(work):
    p = record(work, "--tool=R", "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(work)
    assert doc["params"]["tool"] == "R"
    assert doc["params"]["tool_version"] == "unknown"
    assert "WARNING" in p.stderr and "--tool-version" in p.stderr


def _script(path, body):
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)
    return str(path)


@pytest.mark.skipif(os.name != "posix", reason="shell scripts")
def test_probe_version(tmp_path):
    ok = _script(tmp_path / "ok", 'echo\necho "ok 1.2.3"\necho more\n')
    err = _script(tmp_path / "err", 'echo "err 4.5" >&2\n')
    fails = _script(tmp_path / "fails", "echo nope; exit 1\n")
    silent = _script(tmp_path / "silent", "exit 0\n")
    slow = _script(tmp_path / "slow", "sleep 5\necho late\n")
    assert util.probe_version(ok) == "ok 1.2.3"
    assert util.probe_version(err) == "err 4.5"
    assert util.probe_version(fails) is None
    assert util.probe_version(silent) is None
    assert util.probe_version(str(tmp_path / "missing")) is None
    assert util.probe_version(slow, timeout=0.5) is None


def test_sh_c_records_sh(work):
    # without --tool, a sh -c step is recorded as sh, whatever it runs
    p = record(work, "-o", "covs.csv", command=["sh", "-c", f'cd . && {PY} -c "{DERIVE}"'])
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(work)
    assert doc["params"]["tool"] == "sh"
    # sh may or may not answer --version; whatever it says is its first line
    assert doc["params"]["tool_version"]


# ------------------------------------------------------------------- crate


def test_crate_instrument_object_and_result(work):
    p = record(work, "-i", "sample_info.csv", "-i", "counts.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    crate, g = crate_graph(work)
    (action,) = [e for e in g.values() if e["@type"] == "CreateAction"]
    assert action["name"] == f"{TOOL} run (recorded by detk-util record)"

    tool = g[action["instrument"]["@id"]]
    assert tool["@type"] == "SoftwareApplication"
    assert tool["name"] == TOOL
    assert tool["softwareVersion"] == f"Python {sys.version.split()[0]}"

    objects = [o["@id"] for o in action["object"]]
    assert objects[:2] == ["../sample_info.csv", "../counts.csv"]
    values = {g[o]["name"]: g[o]["value"] for o in objects[2:]}
    assert all(g[o]["@type"] == "PropertyValue" for o in objects[2:])
    assert shlex.split(values["detk-util record command"]) == [TOOL, "-c", DERIVE]
    assert values["detk-util record tool"] == TOOL

    assert [r["@id"] for r in action["result"]] == ["../covs.csv"]
    assert g["../covs.csv"]["sha256"] == sha256(work / "covs.csv")
    assert g["../covs.csv"]["contentSize"] == str((work / "covs.csv").stat().st_size)
    assert g["../sample_info.csv"]["sha256"] == sha256(work / "sample_info.csv")
    assert crate["@context"][1] == WFRUN_CONTEXT


# ------------------------------------------------- the program (DETK-0390)

# print the arguments and a file of the working directory, so a re-run of
# the recorded line can be compared with the recorded run
SHOW = '#!/bin/sh\necho "args: $*"\nhead -n 1 sample_info.csv\n'


def _program(path, body=SHOW):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(0o755)
    return path


@pytest.fixture
def deep(tmp_path):
    "a working directory deep in its tree, with sample_info.csv in it"
    work = tmp_path / "a" / "b" / "c" / "d" / "proj"
    work.mkdir(parents=True)
    (work / "sample_info.csv").write_text(SAMPLE_INFO)
    return work


def _report_payload(work):
    "the module JSON documents embedded in the HTML report"
    html = (work / "detk_report" / "detk_report.html").read_text()
    start = html.index('id="detk-raw">') + len('id="detk-raw">')
    return html[start : html.index("</script>", start)]


def _record_program(work, program, *args, path=None):
    """detk-util record -o out.txt -- PROGRAM ARGS > out.txt in *work*, with
    *path* (a list of directories) first on PATH; the CompletedProcess"""
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(
        [*(str(d) for d in path or ()), os.path.dirname(PY), env.get("PATH", "")]
    )
    with open(work / "out.txt", "w") as out:
        return subprocess.run(
            ["detk-util", "record", "--tool-version=1", "-o", "out.txt", "--", program, *args],
            cwd=work,
            env=env,
            stdout=out,
            stderr=subprocess.PIPE,
            text=True,
        ), env


def _rerun(work, argv, env):
    "the recorded *argv* run again from workdir: its stdout"
    p = subprocess.run(argv, cwd=work, env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout


def test_program_on_path_typed_absolute_is_recorded_by_name(deep):
    cp = shutil.which("cp")
    if cp is None:
        pytest.skip("cp is not on PATH")
    p, _ = _record_program(deep, cp, "sample_info.csv", "copy.csv")
    assert p.returncode == 0, p.stderr
    assert (deep / "copy.csv").read_text() == SAMPLE_INFO

    (doc,) = module_docs(deep)
    params = doc["params"]
    # the program by name; the rest of argv, params and properties as before
    assert params["argv"] == ["cp", "sample_info.csv", "copy.csv"]
    assert params["command"] == "cp sample_info.csv copy.csv"
    assert params["tool"] == "cp" and params["tool_version"] == "1"
    assert params["outputs"] == ["out.txt"] and params["inputs"] == []
    assert [d["path"] for d in doc["properties"]["outputs"]] == ["out.txt"]
    # detk-util's own argv names it so too, after --
    assert doc["argv"][-4:] == ["--", "cp", "sample_info.csv", "copy.csv"]
    # and no ../ chain anywhere: the embedded payload, the crate
    assert "../../" not in _report_payload(deep)
    assert json.loads(_report_payload(deep))
    _, g = crate_graph(deep)
    (action,) = [e for e in g.values() if e["@type"] == "CreateAction"]
    values = {g[o["@id"]]["name"]: g[o["@id"]]["value"] for o in action["object"]}
    assert values["detk-util record command"] == "cp sample_info.csv copy.csv"
    crate_text = (deep / "detk_report" / "ro-crate-metadata.json").read_text()
    assert "../../" not in crate_text and cp not in crate_text


def test_program_found_by_name_re_runs_the_same(deep):
    bin_dir = deep.parent / "bin"
    show = _program(bin_dir / "show")
    p, env = _record_program(deep, str(show), "x", "y", path=[bin_dir])
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(deep)
    assert doc["params"]["argv"] == ["show", "x", "y"]
    recorded = (deep / "out.txt").read_text()
    assert _rerun(deep, doc["params"]["argv"], env) == recorded
    assert _rerun(deep, shlex.split(doc["params"]["command"]), env) == recorded


def test_program_off_path_is_recorded_relative(deep):
    show = _program(deep.parent.parent / "tools" / "show")
    p, env = _record_program(deep, str(show), "x")
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(deep)
    assert doc["params"]["argv"] == ["../../tools/show", "x"]
    assert doc["argv"][-2:] == ["../../tools/show", "x"]
    # it re-runs from workdir as recorded
    assert _rerun(deep, doc["params"]["argv"], env) == (deep / "out.txt").read_text()


def test_program_path_finds_as_another_file_is_recorded_relative(deep):
    # PATH finds a 'show' by that name, but not the one typed
    _program(deep.parent / "bin" / "show", "#!/bin/sh\necho other\n")
    show = _program(deep.parent / "mine" / "show")
    p, env = _record_program(deep, str(show), "x", path=[deep.parent / "bin"])
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(deep)
    assert doc["params"]["argv"] == ["../mine/show", "x"]
    assert _rerun(deep, doc["params"]["argv"], env) == (deep / "out.txt").read_text()


def test_program_typed_by_name_is_kept(deep):
    show = _program(deep.parent / "bin" / "show")
    p, env = _record_program(deep, "show", "x", str(deep / "sample_info.csv"), path=[show.parent])
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(deep)
    # the name as typed; an absolute argument after it relative as before
    assert doc["params"]["argv"] == ["show", "x", "sample_info.csv"]
    assert doc["argv"][-3:] == ["show", "x", "sample_info.csv"]
    assert _rerun(deep, doc["params"]["argv"], env).startswith("args: x sample_info.csv\n")


def test_only_the_program_is_recorded_by_name(deep):
    # an absolute path among the arguments is relative even when it is a
    # program PATH finds: only the first word is the program
    cp = shutil.which("cp")
    if cp is None:
        pytest.skip("cp is not on PATH")
    p, _ = _record_program(deep, cp, cp, "cp.copy")
    assert p.returncode == 0, p.stderr
    (doc,) = module_docs(deep)
    assert doc["params"]["argv"][0] == "cp"
    assert doc["params"]["argv"][1] == _recorded(cp, deep)
    assert doc["params"]["argv"][1].startswith("../")


def test_crate_without_a_record_keeps_its_context(tmp_path):
    from de_toolkit.crate import RO_CRATE_CONTEXT

    crate = build_crate(
        [{"name": "basestats", "id": "a", "params": {}, "in_file_path": "c.csv"}], str(tmp_path)
    )
    assert crate["@context"] == RO_CRATE_CONTEXT


def test_crate_validates_with_a_recorded_step(work):
    pytest.importorskip("rocrate_validator")
    from rocrate_validator import models, services

    p = record(work, "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    settings = services.ValidationSettings(
        rocrate_uri=str(work / "detk_report"),
        profile_identifier="process-run-crate",
        requirement_severity=models.Severity.REQUIRED,
    )
    result = services.validate(settings)
    assert not result.has_issues(), "\n".join(str(i) for i in result.get_issues())


def _producer(g, ref):
    "The CreateAction whose result holds the file *ref*"
    (action,) = [
        e
        for e in g.values()
        if e["@type"] == "CreateAction" and ref in [r["@id"] for r in e.get("result", [])]
    ]
    return action


def _readers(g, ref):
    return [
        e
        for e in g.values()
        if e["@type"] == "CreateAction" and ref in [o["@id"] for o in e.get("object", [])]
    ]


def test_lineage_into_a_later_detk_step(work):
    # record a command that writes the column data, then run a detk step on
    # it: the crate shows the recorded step as that file's producer
    p = record(work, "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    p = run(
        ["detk-filter", "-o", "filtered.csv", "mean(age_group) > 10", "counts.csv", "covs.csv"],
        work,
    )
    assert p.returncode == 0, p.stderr

    _, g = crate_graph(work)
    producer = _producer(g, "../covs.csv")
    assert g[producer["instrument"]["@id"]]["name"] == TOOL
    assert "recorded by detk-util record" in producer["name"]
    (reader,) = _readers(g, "../covs.csv")
    assert g[reader["instrument"]["@id"]]["name"] == "detk-filter"
    assert [r["@id"] for r in reader["result"]] == ["../filtered.csv"]
    # the producer's input is the original sample information
    assert "../sample_info.csv" in [o["@id"] for o in producer["object"]]


@needs_r("DESeq2")
def test_lineage_into_detk_de(work):
    p = record(work, "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    p = run(
        ["detk-de", "deseq2", "-o", "de.csv", "counts ~ age_group", "counts.csv", "covs.csv"],
        work,
    )
    assert p.returncode == 0, p.stderr
    _, g = crate_graph(work)
    producer = _producer(g, "../covs.csv")
    assert g[producer["instrument"]["@id"]]["name"] == TOOL
    readers = _readers(g, "../covs.csv")
    assert any(g[r["instrument"]["@id"]]["name"] == "detk-de deseq2" for r in readers)


# ------------------------------------------------------------------ report


def test_report_lists_the_step_without_a_view(work):
    p = record(work, "-i", "sample_info.csv", "-o", "covs.csv")
    assert p.returncode == 0, p.stderr
    modules, raw = DetkReport(str(work / "detk_report")).build_modules()
    (m,) = modules
    assert m["module"] == "record"
    assert m["family"] == "util"
    assert m["view"] == {"type": "raw"}
    assert raw[m["id"]]["params"]["tool"] == TOOL
    html = (work / "detk_report" / "detk_report.html").read_text()
    assert "Recorded external step" in html
    p = run(["detk-report", "generate"], work)
    assert p.returncode == 0, p.stderr
