"""Tests for the Process Run Crate emitter (de_toolkit.crate)."""

import json
import os
import subprocess
import sys

import pytest

from de_toolkit.crate import (
    CRATE_FILENAME,
    PROFILE_URI,
    STDOUT_MARKER,
    SUBTOOLS,
    build_crate,
    write_crate,
)


def doc(name, doc_id, **kw):
    d = {
        "name": name,
        "id": doc_id,
        "schema_version": "1.0",
        "detk_version": "0.9.12",
        "last_modified": kw.pop("last_modified", 0),
        "start_time": "2026-08-11T15:00:00+00:00",
        "end_time": "2026-08-11T15:00:05+00:00",
        "params": kw.pop("params", {}),
        "properties": {},
        "in_file_path": None,
        "out_file_path": None,
        "column_data_path": None,
        "workdir": kw.pop("workdir", None),
    }
    d.update(kw)
    return d


def graph_of(crate):
    return {e["@id"]: e for e in crate["@graph"]}


def test_crate_skeleton(tmp_path):
    crate = build_crate([doc("basestats", "abc")], str(tmp_path))
    g = graph_of(crate)

    # metadata descriptor
    desc = g[CRATE_FILENAME]
    assert desc["@type"] == "CreativeWork"
    assert desc["about"] == {"@id": "./"}
    assert "w3id.org/ro/crate" in desc["conformsTo"]["@id"]

    # root conforms to the Process Run Crate profile and mentions the action
    root = g["./"]
    assert root["@type"] == "Dataset"
    assert root["conformsTo"]["@id"] == PROFILE_URI
    assert len(root["mentions"]) == 1

    # action instrument resolves to a per-subtool SoftwareApplication
    action = g[root["mentions"][0]["@id"]]
    assert action["@type"] == "CreateAction"
    assert action["startTime"] and action["endTime"]
    sw = g[action["instrument"]["@id"]]
    assert sw["@type"] == "SoftwareApplication"
    assert sw["name"] == "detk-stats basestats"
    assert sw["softwareVersion"] == "0.9.12"


def test_action_ids_are_deterministic(tmp_path):
    def ids(c):
        return {e["@id"] for e in c["@graph"] if e["@type"] == "CreateAction"}

    c1 = build_crate([doc("basestats", "abc")], str(tmp_path))
    c2 = build_crate([doc("basestats", "abc")], str(tmp_path))
    assert ids(c1) == ids(c2)
    assert all(i.startswith("urn:uuid:") for i in ids(c1))


def test_params_become_property_values(tmp_path):
    crate = build_crate(
        [doc("filtercounts", "f1", params={"count_filter_spec": "mean(all) > 10", "empty": None})],
        str(tmp_path),
    )
    pvs = [e for e in crate["@graph"] if e["@type"] == "PropertyValue"]
    # None-valued params are omitted
    assert len(pvs) == 1
    assert pvs[0]["value"] == "mean(all) > 10"
    action = next(e for e in crate["@graph"] if e["@type"] == "CreateAction")
    assert {"@id": pvs[0]["@id"]} in action["object"]


def test_file_chaining_shares_entities(tmp_path):
    (tmp_path / "raw.csv").write_text("x\n")
    (tmp_path / "norm.csv").write_text("x\n")
    docs = [
        doc(
            "deseq2norm",
            "n1",
            in_file_path="raw.csv",
            out_file_path="norm.csv",
            workdir=str(tmp_path),
            last_modified=1,
        ),
        doc(
            "basestats",
            "s1",
            in_file_path="norm.csv",
            workdir=str(tmp_path),
            last_modified=2,
        ),
    ]
    crate = build_crate(docs, str(tmp_path))
    g = graph_of(crate)

    # one shared File entity: norm.csv is result of the norm action and
    # object of the stats action
    files = [e for e in crate["@graph"] if e["@type"] == "File"]
    assert {f["@id"] for f in files} == {"raw.csv", "norm.csv"}
    actions = {
        g[a["instrument"]["@id"]]["name"]: a
        for a in crate["@graph"]
        if a["@type"] == "CreateAction"
    }
    assert {r["@id"] for r in actions["detk-norm deseq2"]["result"]} == {"norm.csv"}
    assert {"@id": "norm.csv"} in actions["detk-stats basestats"]["object"]

    # existing files under the root are in hasPart
    assert {p["@id"] for p in g["./"]["hasPart"]} == {"raw.csv", "norm.csv"}
    assert files[0]["encodingFormat"] == "text/csv"


def test_file_outside_root_is_relative_to_the_root(tmp_path):
    # the crate is rooted in the report directory; a file in the working
    # directory, or anywhere else, is named by its path relative to the root
    # (DETK-0280), never by an absolute file:// URI
    work = tmp_path / "work"
    report = work / "detk_report"
    report.mkdir(parents=True)
    (work / "counts.csv").write_text("x\n")
    outside = tmp_path / "elsewhere" / "sample_info.csv"
    outside.parent.mkdir()
    outside.write_text("x\n")
    crate = build_crate(
        [
            doc(
                "basestats",
                "s1",
                in_file_path="counts.csv",
                column_data_path="../elsewhere/sample_info.csv",
                workdir="..",
            )
        ],
        str(report),
    )
    action = next(e for e in crate["@graph"] if e["@type"] == "CreateAction")
    refs = {o["@id"] for o in action["object"] if not o["@id"].startswith("#")}
    assert refs == {"../counts.csv", "../../elsewhere/sample_info.csv"}
    assert not any("file://" in e["@id"] for e in crate["@graph"])
    g = graph_of(crate)
    assert {p["@id"] for p in g["./"]["hasPart"]} == refs


def test_absolute_workdir_of_an_older_document_resolves(tmp_path):
    # schema 1.0 and 1.1 documents hold workdir absolute: it still resolves
    report = tmp_path / "detk_report"
    report.mkdir()
    crate = build_crate(
        [doc("basestats", "s1", in_file_path="counts.csv", workdir=str(tmp_path))],
        str(report),
    )
    action = next(e for e in crate["@graph"] if e["@type"] == "CreateAction")
    assert action["object"] == [{"@id": "../counts.csv"}]


def test_write_crate_empty_docs_writes_nothing(tmp_path):
    assert write_crate([], str(tmp_path)) is None
    assert not (tmp_path / CRATE_FILENAME).exists()


def test_every_registered_module_has_a_subtool_mapping():
    # every DetkModule subclass that emits report JSON must resolve to a
    # SoftwareApplication; keep SUBTOOLS in sync with the module registry
    from de_toolkit import report_specs

    known = set(report_specs.REGISTRY) | set(report_specs._FALLBACK_FAMILIES)
    missing = known - set(SUBTOOLS)
    assert not missing, f"modules without a SUBTOOLS mapping: {missing}"


def test_crate_validates_against_profile(tmp_path):
    """Full conformance check with rocrate-validator, when available: the
    crate rooted in the report directory, its files ../ references."""
    pytest.importorskip("rocrate_validator")

    (tmp_path / "raw.csv").write_text("x\n")
    (tmp_path / "norm.csv").write_text("x\n")
    report = tmp_path / "detk_report"
    report.mkdir()
    write_crate(
        [
            doc(
                "deseq2norm",
                "n1",
                in_file_path="raw.csv",
                out_file_path="norm.csv",
                workdir="..",
                params={"foo": 1},
            )
        ],
        str(report),
    )
    crate = graph_of(json.loads((report / CRATE_FILENAME).read_text()))
    assert {p["@id"] for p in crate["./"]["hasPart"]} == {"../raw.csv", "../norm.csv"}
    assert_valid_process_run_crate(report)


def assert_valid_process_run_crate(report):
    "The crate in *report* conforms to the Process Run Crate profile (REQUIRED)"
    from rocrate_validator import services, models

    settings = services.ValidationSettings(
        rocrate_uri=str(report),
        profile_identifier="process-run-crate",
        requirement_severity=models.Severity.REQUIRED,
    )
    result = services.validate(settings)
    assert not result.has_issues(), "\n".join(str(i) for i in result.get_issues())


# ------------------------------------------- standard output is not a file

COUNTS = "gene,s1,s2,s3,s4\n" + "".join(
    f"g{g},{10 + g},{20 + 2 * g},{15 + g},{30 + 3 * g}\n" for g in range(30)
)


def run_detk(args, cwd):
    "Run a detk console script in *cwd*, as a user would; its stdout"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    assert p.returncode == 0, f"{args} failed\n{p.stdout}\n{p.stderr}"
    return p.stdout


@pytest.fixture
def work(tmp_path):
    w = tmp_path / "work"
    w.mkdir()
    (w / "counts.csv").write_text(COUNTS)
    return w


def module_doc(report):
    (path,) = (report / "json").glob("*.json")
    return json.loads(path.read_text())


def cpm_action(graph):
    (action,) = [e for e in graph.values() if e["@type"] == "CreateAction"]
    return action


def test_cpm_to_stdout_lists_no_stdout_file(work):
    out = run_detk(["detk-norm", "cpm", "counts.csv"], work)
    assert out.startswith("gene")
    report = work / "detk_report"
    # module JSON keeps the documented marker
    assert module_doc(report)["out_file_path"] == STDOUT_MARKER
    graph = graph_of(json.loads((report / CRATE_FILENAME).read_text()))
    assert not [i for i in graph if i.endswith("stdout")]
    action = cpm_action(graph)
    assert "result" not in action
    # the input is still listed
    assert {"@id": "../counts.csv"} in action["object"]
    assert graph["../counts.csv"]["@type"] == "File"
    assert {p["@id"] for p in graph["./"]["hasPart"]} == {"../counts.csv"}


def test_cpm_to_a_file_lists_it(work):
    run_detk(["detk-norm", "cpm", "-o", "out.csv", "counts.csv"], work)
    report = work / "detk_report"
    assert module_doc(report)["out_file_path"] == "out.csv"
    graph = graph_of(json.loads((report / CRATE_FILENAME).read_text()))
    assert cpm_action(graph)["result"] == [{"@id": "../out.csv"}]
    assert graph["../out.csv"]["@type"] == "File"
    assert {p["@id"] for p in graph["./"]["hasPart"]} == {"../counts.csv", "../out.csv"}


@pytest.mark.parametrize("typed", ["./stdout", "--output=./stdout", "{w}/stdout"])
def test_a_file_really_named_stdout_is_listed(work, typed):
    # -o stdout is the marker; a file named stdout is typed another way
    opt = typed.format(w=os.path.realpath(work))
    args = [opt] if opt.startswith("--") else ["-o", opt]
    out = run_detk(["detk-norm", "cpm", *args, "counts.csv"], work)
    assert out == ""
    assert (work / "stdout").read_text().startswith("gene")
    report = work / "detk_report"
    doc_ = module_doc(report)
    assert doc_["out_file_path"] == "./stdout"
    # an absolute path in argv is recorded relative, and still not the marker
    assert STDOUT_MARKER not in doc_["argv"]
    graph = graph_of(json.loads((report / CRATE_FILENAME).read_text()))
    assert cpm_action(graph)["result"] == [{"@id": "../stdout"}]
    assert graph["../stdout"]["@type"] == "File"
    assert {"@id": "../stdout"} in graph["./"]["hasPart"]


def test_stdout_marker_left_out_of_out_file_paths(tmp_path):
    # detk-util tidy lists its outputs, the first standard output
    (tmp_path / "cols.csv").write_text("x\n")
    crate = build_crate(
        [
            doc(
                "tidy",
                "t1",
                in_file_path="counts.csv",
                out_file_path=STDOUT_MARKER,
                out_file_paths=[STDOUT_MARKER, "cols.csv"],
                workdir=str(tmp_path),
            )
        ],
        str(tmp_path),
    )
    g = graph_of(crate)
    assert not [i for i in g if i.endswith("stdout")]
    action = next(e for e in crate["@graph"] if e["@type"] == "CreateAction")
    assert action["result"] == [{"@id": "cols.csv"}]


def test_recorded_output_named_stdout_is_a_file(tmp_path):
    # detk-util record checksums every output it lists: each is a file,
    # whatever its name
    (tmp_path / "stdout").write_text("x\n")
    crate = build_crate(
        [
            doc(
                "record",
                "r1",
                out_file_path="stdout",
                out_file_paths=["stdout"],
                workdir=str(tmp_path),
                params={"tool": "cp", "tool_version": "9"},
            )
        ],
        str(tmp_path),
    )
    action = next(e for e in crate["@graph"] if e["@type"] == "CreateAction")
    assert action["result"] == [{"@id": "stdout"}]


@pytest.mark.parametrize(
    "typed,recorded",
    [
        ("stdout", "stdout"),
        ("./stdout", "./stdout"),
        ("sub/../stdout", "./stdout"),
        ("{w}/stdout", "./stdout"),
        ("sub/stdout", "sub/stdout"),
        ("-", "-"),
    ],
)
def test_file_relpath_keeps_the_marker_apart(tmp_path, typed, recorded):
    from de_toolkit.report import _file_relpath

    w = os.path.realpath(tmp_path)
    assert _file_relpath(typed.format(w=w), w) == recorded


def test_crate_with_output_to_stdout_validates(work):
    pytest.importorskip("rocrate_validator")
    run_detk(["detk-norm", "cpm", "counts.csv"], work)
    report = work / "detk_report"
    graph = graph_of(json.loads((report / CRATE_FILENAME).read_text()))
    assert "result" not in cpm_action(graph)
    assert_valid_process_run_crate(report)
