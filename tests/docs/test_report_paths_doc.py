"""
docs/report.md's example of a path inside a quoted argument, run as the page
shows it: ``detk-util record ... -- sh -c "cp /abs/a.csv /abs/b.csv"`` in the
working directory the page names (here a temporary one in its place)
records the -i and -o paths relative and the script as typed, absolute
paths and all, as the JSON the page shows.
"""

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parents[2] / "docs" / "report.md"
PAGE_WORKDIR = "/home/me/proj"


def _example():
    "The command the page runs and the JSON it says is recorded, in /home/me/proj"
    text = PAGE.read_text()
    m = re.search(
        r"```console\n\s*\$ (detk-util record [^\n]*sh -c [^\n]*)\n\s*```"
        r".*?```json\n(.*?)\n\s*```",
        text,
        re.S,
    )
    assert m, "docs/report.md has no sh -c example of detk-util record"
    return m.group(1), json.loads(m.group(2))


def test_quoted_script_is_recorded_as_typed(tmp_path):
    work = Path(os.path.realpath(tmp_path)) / "proj"
    work.mkdir()
    (work / "a.csv").write_text("gene,s1\ng1,1\n")
    command, shown = _example()
    argv = shlex.split(command.replace(PAGE_WORKDIR, str(work)))
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    p = subprocess.run(argv, cwd=work, env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert (work / "b.csv").read_text() == "gene,s1\ng1,1\n"

    (path,) = (work / "detk_report" / "json").glob("*.json")
    recorded = json.loads(path.read_text())
    expected = json.loads(json.dumps(shown).replace(PAGE_WORKDIR, str(work)))
    for key, value in expected.items():
        assert recorded[key] == value, f"{key}: recorded {recorded[key]!r}, the page says {value!r}"
    # the script keeps its absolute paths; nothing else recorded is absolute
    script = recorded["argv"][-1]
    assert script == f"cp {work}/a.csv {work}/b.csv"
    assert not [a for a in recorded["argv"][:-1] if os.path.isabs(a)]
    assert recorded["workdir"] == ".."
