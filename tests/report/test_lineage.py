"""An enrichment table traces back, through the report's Process Run Crate,
to the counts and sample information it came from (#207).

The test runs a filter -> DESeq2 -> fgsea chain in one report directory,
validates the crate against the Process Run Crate profile and walks its
edges backwards: from a File to the CreateAction whose ``result`` lists it,
then to that action's ``object`` Files, and so on to the files no action
made.

On v1.0.0 the walk stops at fgsea: its action listed the GMT as its only
input file, not the DESeq2 results it ranked, so the table had no path back
to the counts or the sample sheet (fixed by #199, DETK-0720; #182 made each
run keep its own record). ``assert_traces_back`` is written for reuse, e.g.
by a release check of the installed wheel."""

import json
import os
import subprocess
import sys

import pytest

from de_toolkit.crate import CRATE_FILENAME
from r_packages import needs_r
from test_crate import assert_valid_process_run_crate

# six samples in two groups, one gene in four shifted between them; the
# counts and the sample sheet name the same samples
SAMPLES = ["s1", "s2", "s3", "s4", "s5", "s6"]
COUNTS = (
    "gene,"
    + ",".join(SAMPLES)
    + "\n"
    + "".join(
        f"g{g},{10 + 7 * g},{14 + 5 * g},{12 + 6 * g},"
        f"{(10 + 7 * g) * (3 if g % 4 == 0 else 1) + (g * 13) % 11},"
        f"{(14 + 5 * g) * (3 if g % 4 == 0 else 1) + (g * 7) % 13},"
        f"{(12 + 6 * g) * (3 if g % 4 == 0 else 1) + (g * 5) % 17}\n"
        for g in range(60)
    )
)
SAMPLE_INFO = "sample,group\n" + "".join(
    f"{s},{'a' if i < 3 else 'b'}\n" for i, s in enumerate(SAMPLES)
)
GMT = "".join(
    f"set{k}\tdescription\t" + "\t".join(f"g{g}" for g in range(k, 60, 4)) + "\n" for k in range(4)
)

# the chain, as a user types it, in one working directory (one report)
CHAIN = [
    ["detk-filter", "-o", "filtered.csv", "mean(all) > 10", "counts.csv"],
    ["detk-de", "deseq2", "-o", "de.csv", "counts ~ group", "filtered.csv", "sample_info.csv"],
    [
        "detk-enrich",
        "fgsea",
        "--minSize",
        "2",
        "-c",
        "group__b__stat",
        "-o",
        "gsea.csv",
        "sets.gmt",
        "de.csv",
    ],
]


def run(args, cwd):
    "Run a detk console script in *cwd*, as a user would"
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    assert p.returncode == 0, f"{args} failed\n{p.stdout}\n{p.stderr}"
    return p


def lineage(graph, start):
    """Every File *start* came from, walking result -> action -> object
    edges: ``{file id: the ids of the actions that led to it}``, the files
    no action made among them."""
    entities = {e["@id"]: e for e in graph}
    made_by = {}
    for e in graph:
        if e.get("@type") == "CreateAction":
            for r in e.get("result", []):
                made_by.setdefault(r["@id"], []).append(e["@id"])

    found = {}
    todo = [(start, ())]
    while todo:
        fid, path = todo.pop()
        for action in made_by.get(fid, []):
            if action in path:  # a file a step both read and wrote
                continue
            for o in entities[action].get("object", []):
                if entities.get(o["@id"], {}).get("@type") == "File" and o["@id"] not in found:
                    found[o["@id"]] = path + (action,)
                    todo.append((o["@id"], path + (action,)))
    return found


def assert_traces_back(report, table, sources):
    """The crate in *report* (a report directory) traces File *table* back
    to every one of *sources*, each a File no action made. Ids are as the
    crate names them, relative to the report directory (``../counts.csv``)."""
    graph = json.loads((report / CRATE_FILENAME).read_text())["@graph"]
    ids = {e["@id"] for e in graph}
    assert table in ids, f"{table} is not in the crate"
    found = lineage(graph, table)
    missing = [s for s in sources if s not in found]
    assert not missing, (
        f"{table} does not trace back to {missing}; it traces back to {sorted(found)}"
    )
    made = {
        r["@id"] for e in graph if e.get("@type") == "CreateAction" for r in e.get("result", [])
    }
    assert not set(sources) & made, "a source file is the result of an action"
    return found


@pytest.fixture
def work(tmp_path):
    w = tmp_path / "work"
    w.mkdir()
    (w / "counts.csv").write_text(COUNTS)
    (w / "sample_info.csv").write_text(SAMPLE_INFO)
    (w / "sets.gmt").write_text(GMT)
    return w


@needs_r("DESeq2", "fgsea")
def test_fgsea_table_traces_back_to_counts_and_sample_info(work):
    for args in CHAIN:
        run(args, work)
    run(["detk-report", "generate"], work)
    report = work / "detk_report"

    pytest.importorskip("rocrate_validator")
    assert_valid_process_run_crate(report)

    found = assert_traces_back(
        report, "../gsea.csv", ["../counts.csv", "../sample_info.csv", "../sets.gmt"]
    )
    # through each step of the chain: fgsea, then DESeq2, then the filter
    graph = {e["@id"]: e for e in json.loads((report / CRATE_FILENAME).read_text())["@graph"]}
    names = [graph[a]["name"] for a in found["../counts.csv"]]
    assert names == ["detk-enrich fgsea run", "detk-de deseq2 run", "detk-filter run"]
    assert [graph[a]["name"] for a in found["../sample_info.csv"]] == [
        "detk-enrich fgsea run",
        "detk-de deseq2 run",
    ]


# --------------------------------------------- the walk itself, without R


def _action(aid, objects, results):
    return {
        "@id": aid,
        "@type": "CreateAction",
        "name": aid,
        "object": [{"@id": o} for o in objects] + [{"@id": "#param-x"}],
        "result": [{"@id": r} for r in results],
    }


def _files(*ids):
    return [{"@id": i, "@type": "File"} for i in ids]


def test_lineage_walks_result_action_object_edges():
    graph = _files("c", "s", "f", "d", "g", "t") + [
        {"@id": "#param-x", "@type": "PropertyValue"},
        _action("#filter", ["c"], ["f"]),
        _action("#de", ["f", "s"], ["d"]),
        _action("#fgsea", ["g", "d"], ["t"]),
    ]
    found = lineage(graph, "t")
    assert set(found) == {"c", "s", "f", "d", "g"}
    assert found["c"] == ("#fgsea", "#de", "#filter")
    assert "#param-x" not in found


def test_lineage_stops_where_an_action_lists_no_input(tmp_path):
    "the v1.0.0 crate: fgsea's action lists the GMT, not the DE results"
    graph = _files("c", "s", "d", "g", "t") + [
        _action("#de", ["c", "s"], ["d"]),
        _action("#fgsea", ["g"], ["t"]),
    ]
    assert set(lineage(graph, "t")) == {"g"}
    (tmp_path / CRATE_FILENAME).write_text(json.dumps({"@graph": graph}))
    with pytest.raises(AssertionError, match=r"does not trace back to \['c', 's'\]"):
        assert_traces_back(tmp_path, "t", ["c", "s"])


def test_lineage_survives_a_file_read_and_written_by_one_step():
    graph = _files("a", "b") + [_action("#inplace", ["a", "b"], ["b"])]
    assert set(lineage(graph, "b")) == {"a", "b"}
