"""Tests for the Process Run Crate emitter (de_toolkit.crate)."""

import json

import pytest

from de_toolkit.crate import (
    CRATE_FILENAME,
    PROFILE_URI,
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
    from rocrate_validator import services, models

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
    settings = services.ValidationSettings(
        rocrate_uri=str(report),
        profile_identifier="process-run-crate",
        requirement_severity=models.Severity.REQUIRED,
    )
    result = services.validate(settings)
    assert not result.has_issues(), "\n".join(str(i) for i in result.get_issues())
