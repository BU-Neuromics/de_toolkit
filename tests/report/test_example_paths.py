"""The published example (docs/example/) holds no path of the machine it was
built on (Adam, 2026-11-20; DETK-0280): every recorded path in the report's
embedded module JSON and in the Process Run Crate is relative, and no
absolute path appears anywhere in the files' text."""

import json
import re
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "docs" / "example"

# fields of the module JSON whose values are paths (one or a list)
PATH_FIELDS = {
    "workdir",
    "argv",
    "in_file_path",
    "in_file_paths",
    "out_file_path",
    "out_file_paths",
    "column_data_path",
}

# raw text: a home, temp or root directory, a Windows drive path, a file:// URI
RAW = re.compile(
    r"/home/|/Users/|/tmp/|/private/|/root/|file://|(?<![A-Za-z0-9])[A-Za-z]:[\\/]",
)


class _Scripts(HTMLParser):
    "Each <script> element of a page: its attributes and its body"

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts, self._open = [], None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self._open = (dict(attrs), [])

    def handle_data(self, data):
        if self._open is not None:
            self._open[1].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._open is not None:
            self.scripts.append((self._open[0], "".join(self._open[1])))
            self._open = None


def scripts(html):
    "(attributes, body) of every <script> element in *html*"
    parser = _Scripts()
    parser.feed(html)
    parser.close()
    return parser.scripts


def json_blocks(html):
    "The report's embedded JSON data blocks, by id (detk-modules, detk-raw)"
    return {a.get("id"): body for a, body in scripts(html) if a.get("type") == "application/json"}


def _blank_code(html):
    """*html* with the body of each code <script> blanked, its newlines kept:
    the vendored Vega libraries and the report's own script come from the
    package, not the run, and Vega's minified code holds "file://" and "o:/["
    of its own, so the raw-text check skips them"""
    for a, body in scripts(html):
        if a.get("type") != "application/json" and body:
            html = html.replace(body, "\n" * body.count("\n"))
    return html


def is_absolute(value):
    "A path written as absolute on any platform, or a file:// URI"
    if not isinstance(value, str):
        return False
    if value.lower().startswith("file:"):
        return True
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


def _values(v):
    if isinstance(v, list):
        for x in v:
            yield from _values(x)
    elif v is not None:
        yield v


def path_fields(doc, where=""):
    "(location, value) for every value of a path field anywhere in *doc*"
    if isinstance(doc, dict):
        for k, v in doc.items():
            loc = f"{where}.{k}"
            if k in PATH_FIELDS:
                for x in _values(v):
                    if isinstance(x, str):
                        yield loc, x
            yield from path_fields(v, loc)
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            yield from path_fields(v, f"{where}[{i}]")


def crate_files(crate):
    "@id of every File entity in a crate"
    for e in crate.get("@graph", []):
        types = e.get("@type", [])
        types = [types] if isinstance(types, str) else types
        if "File" in types:
            yield e["@id"]


def absolute_paths(directory):
    """Every absolute path found in the files under *directory*, as
    'file: where: value' strings; empty when the example is clean."""
    found = []
    for f in sorted(Path(directory).rglob("*")):
        if not f.is_file():
            continue
        name = f.relative_to(directory).as_posix()
        text = f.read_text(encoding="utf-8")

        scan = _blank_code(text) if f.suffix == ".html" else text
        for m in RAW.finditer(scan):
            line = scan.count("\n", 0, m.start()) + 1
            snippet = scan[m.start() : m.start() + 60].split('"')[0]
            found.append(f"{name}:{line}: text: {snippet}")

        if f.suffix == ".html":
            for sid, body in json_blocks(text).items():
                for loc, v in path_fields(json.loads(body), sid):
                    if is_absolute(v):
                        found.append(f"{name}: {loc}: {v}")
        elif f.suffix == ".json":
            doc = json.loads(text)
            for loc, v in path_fields(doc, "$"):
                if is_absolute(v):
                    found.append(f"{name}: {loc}: {v}")
            for i in crate_files(doc):
                if is_absolute(i):
                    found.append(f"{name}: File @id: {i}")
    return found


# ------------------------------------------------------- the published files


def test_published_example_has_its_files():
    assert (EXAMPLE / "detk_report.html").is_file()
    assert (EXAMPLE / "ro-crate-metadata.json").is_file()
    html = (EXAMPLE / "detk_report.html").read_text(encoding="utf-8")
    assert set(json_blocks(html)) == {"detk-modules", "detk-raw"}


def test_published_example_holds_no_absolute_path():
    found = absolute_paths(EXAMPLE)
    assert not found, "absolute paths in docs/example/:\n" + "\n".join(found)


def test_published_example_records_relative_paths():
    "the checks above are not vacuous: the example records paths, relatively"
    html = (EXAMPLE / "detk_report.html").read_text(encoding="utf-8")
    raw = json_blocks(html)["detk-raw"]
    fields = list(path_fields(json.loads(raw)))
    assert any(loc.endswith(".workdir") for loc, _ in fields)
    assert any(".in_file_path" in loc for loc, _ in fields)
    crate = json.loads((EXAMPLE / "ro-crate-metadata.json").read_text())
    assert list(crate_files(crate))


# ------------------------------------------------ the check catches each kind


def _report(raw):
    return (
        "<html>"
        '<script type="application/json" id="detk-modules">[]</script>'
        f'<script type="application/json" id="detk-raw">{json.dumps(raw)}</script>'
        "</html>"
    )


@pytest.mark.parametrize(
    "field, value",
    [
        ("workdir", "/srv/build/airway"),
        ("argv", ["/opt/venv/bin/detk-stats", "summary"]),
        ("in_file_path", "/data/counts.csv"),
        ("in_file_paths", ["counts.csv", "/data/samples.csv"]),
        ("out_file_path", "C:\\work\\out.csv"),
        ("out_file_paths", ["file:///data/out.csv"]),
        ("column_data_path", "/data/samples.csv"),
    ],
)
def test_check_finds_an_absolute_path_field(tmp_path, field, value):
    # paths outside the raw-text patterns, so only the field check finds them
    (tmp_path / "detk_report.html").write_text(_report({"m": {field: value}}))
    found = absolute_paths(tmp_path)
    assert any(f"detk-raw.m.{field}" in x for x in found), found


def test_check_finds_an_absolute_crate_file(tmp_path):
    crate = {"@graph": [{"@id": "/srv/counts.csv", "@type": "File"}]}
    (tmp_path / "ro-crate-metadata.json").write_text(json.dumps(crate))
    assert absolute_paths(tmp_path) == ["ro-crate-metadata.json: File @id: /srv/counts.csv"]


@pytest.mark.parametrize(
    "text",
    [
        "/home/someone/x",
        "/Users/someone/x",
        "/tmp/pytest-1/x",
        "/private/var/x",
        "/root/x",
        "C:\\Users\\x",
        "D:/data/x",
        "file:///x",
    ],
)
def test_check_finds_a_machine_path_in_the_text(tmp_path, text):
    (tmp_path / "notes.txt").write_text(f"made at {text}\n")
    assert absolute_paths(tmp_path)


def test_check_skips_library_code_but_not_data(tmp_path):
    lib = '<script>var jo="file://",x=o:/[%p]/.test(v);</script>'
    (tmp_path / "detk_report.html").write_text(lib + _report({}))
    assert absolute_paths(tmp_path) == []
    (tmp_path / "detk_report.html").write_text(lib + "<p>/home/someone</p>" + _report({}))
    (found,) = absolute_paths(tmp_path)
    assert found.startswith("detk_report.html:1: text: /home/someone")


def test_check_passes_relative_paths(tmp_path):
    raw = {
        "m": {
            "workdir": "..",
            "argv": ["detk-stats", "summary", "counts.csv"],
            "in_file_path": "counts.csv",
            "out_file_paths": ["out/a.csv"],
            "column_data_path": None,
            "url": "https://example.org/a:b",
        }
    }
    (tmp_path / "detk_report.html").write_text(_report(raw))
    crate = {"@graph": [{"@id": "../counts.csv", "@type": "File"}]}
    (tmp_path / "ro-crate-metadata.json").write_text(json.dumps(crate))
    assert absolute_paths(tmp_path) == []
