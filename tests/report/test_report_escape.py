"""The report's embedded JSON cannot end its <script> block (#46).

Feature IDs, sample names and annotation values come from user files and are
embedded in ``<script type="application/json">`` elements; a string holding
``</script>`` must leave the report intact and read back unchanged.
"""

import json
import os
import re

import pytest

from de_toolkit.report import DetkReport, script_json

EVIL = "</script><script>alert(1)</script>"
# a sample name that also needs ordinary JSON escaping (quote, backslash) and
# the characters JSON allows raw but HTML or old JavaScript do not
ODD = 'a"b\\c & <!-- d   e  '


def _modules():
    base = {"detk_version": "0.0.0", "in_file_path": "counts.csv", "params": {}}
    return {
        # sample names and an annotation column value (column data)
        "pca": {
            **base,
            "name": "pca",
            "properties": {
                "column_names": [EVIL, "s2"],
                "column_variables": {
                    "sample_names": [EVIL, "s2"],
                    "columns": [{"column": "status", "values": [EVIL, "B"]}],
                },
                "components": [
                    {"name": "PC1", "scores": [1.0, -1.0], "perc_variance": 0.5},
                    {"name": "PC2", "scores": [0.5, -0.5], "perc_variance": 0.2},
                ],
            },
        },
        # sample names as object keys
        "deseq2norm": {
            **base,
            "name": "deseq2norm",
            "properties": {"size_factors": {EVIL: 1.0, ODD: 0.5}},
        },
        # feature IDs and annotation columns from detk-util annotate
        "annotate": {
            **base,
            "name": "annotate",
            "params": {"annotation": EVIL},
            "properties": {
                "num_features": 2,
                "num_mapped": 1,
                "columns_added": [EVIL],
                "unmapped_examples": [EVIL],
            },
        },
    }


def _render(tmp_path, dev):
    rep = DetkReport(str(tmp_path / "rep"), crate_dir=str(tmp_path))
    mods = _modules()
    for name, m in mods.items():
        with open(os.path.join(rep.json_dir, name + ".json"), "w") as f:
            json.dump(m, f)
    rep.write(dev=dev)
    with open(rep.report_path, encoding="utf-8") as f:
        return mods, f.read()


def _script_body(html, elem_id):
    # what the HTML parser does: the element ends at the first "</script"
    pattern = rf'<script type="application/json" id="{elem_id}">(.*?)</script'
    m = re.search(pattern, html, re.S)
    assert m, f"no #{elem_id} script element"
    return m.group(1)


@pytest.mark.parametrize("dev", [False, True])
def test_user_strings_cannot_end_the_script_block(tmp_path, dev):
    mods, html = _render(tmp_path, dev)

    # the hostile string never appears raw: the only script tags are the
    # template's own (three vendored libraries, two payloads, the app)
    assert EVIL not in html
    assert len(re.findall(r"<script\b", html, re.I)) == 6
    assert len(re.findall(r"</script", html, re.I)) == 6

    raw_body = _script_body(html, "detk-raw")
    modules_body = _script_body(html, "detk-modules")
    for body in (raw_body, modules_body):
        assert "<" not in body and ">" not in body and "&" not in body

    # the embedded data round-trips to the original strings
    raw = json.loads(raw_body)
    by_module = {v["name"]: v for v in raw.values()}
    pca = by_module["pca"]["properties"]
    assert pca["column_variables"]["sample_names"][0] == EVIL
    assert pca["column_variables"]["columns"][0]["values"][0] == EVIL
    assert set(by_module["deseq2norm"]["properties"]["size_factors"]) == {EVIL, ODD}
    ann = by_module["annotate"]
    assert ann["params"]["annotation"] == EVIL
    assert ann["properties"]["unmapped_examples"] == [EVIL]
    assert ann["properties"]["columns_added"] == [EVIL]

    # and the view descriptors carry the strings through to the charts
    views = {m["module"]: m["view"] for m in json.loads(modules_body)}
    samples = [r["sample"] for r in views["deseq2norm"]["spec"]["data"]["values"]]
    assert set(samples) == {EVIL, ODD}

    # the app script after the payload is still the template's, intact
    assert 'JSON.parse(document.getElementById("detk-raw").textContent)' in html
    assert html.rstrip().endswith("</html>")


def test_script_json_round_trips_and_escapes():
    obj = {EVIL: [EVIL, ODD], "k": {"n": 1, ODD: "&amp;"}}
    text = script_json(obj)
    for ch in ("<", ">", "&", " ", " "):
        assert ch not in text
    assert json.loads(text) == obj
    assert json.loads(script_json(obj, indent=2)) == obj
