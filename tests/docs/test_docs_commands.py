"""
The commands of the README, the home page, the quickstart and the worked
example run as written on the CLI:

- every ``detk-*`` command line in their fenced blocks parses with that
  command's parser, by the check tests/skills/test_skills.py makes of the
  skill (DETK-0010);
- the quickstart's commands run in order, on a small counts matrix, column
  data file and GMT file made here: the steps that run R (detk-de deseq2,
  detk-enrich fgsea) where R and its packages are installed, as in the CI
  job with R. Elsewhere those steps, and the steps that read what they
  write, are left out; the rest run and are checked, and then the test
  skips naming what was missing (Rscript, or the R package).
"""

import importlib.util
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from r_packages import missing_r

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = os.path.dirname(sys.executable)
PAGES = ["README.md", "docs/index.md", "docs/quickstart.md", "docs/example.md"]


def _skill_checker():
    "check_markdown of tests/skills/test_skills.py, loaded from its file"
    path = ROOT / "tests" / "skills" / "test_skills.py"
    spec = importlib.util.spec_from_file_location("_skill_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check_markdown


@pytest.mark.parametrize("page", PAGES)
def test_page_commands_parse(page):
    _skill_checker()((ROOT / page).read_text(), page)


# 200 features in 6 samples, 3 control and 3 treated, deterministic (a linear
# congruential generator) with enough spread for DESeq2's dispersion fit;
# every tenth feature is up in the treated samples, and every seventh is zero
# in most samples, so the filter has rows to drop
SAMPLES = ("s1", "s2", "s3", "s4", "s5", "s6")


def _raw_counts():
    x = 12345
    rows = ["gene," + ",".join(SAMPLES)]
    for g in range(200):
        base = 5 + (g * 37) % 500
        vals = []
        for j, _ in enumerate(SAMPLES):
            x = (1103515245 * x + 12345) % 2**31
            effect = 3 if (g % 10 == 0 and j >= 3) else 1
            value = int(base * effect * (0.6 + 0.8 * x / 2**31))
            vals.append(str(0 if g % 7 == 3 and j != 0 else value))
        rows.append(f"g{g}," + ",".join(vals))
    return "\n".join(rows) + "\n"


QUICKSTART_DATA = {
    "raw_counts.csv": _raw_counts(),
    "sample_info.csv": "sample,cond\n"
    + "".join(f"{s},{'control' if i < 3 else 'treated'}\n" for i, s in enumerate(SAMPLES)),
    "msigdb_c2cp.gmt": "".join(
        f"SET_{k}\tna\t" + "\t".join(f"g{g}" for g in range(200) if g % 5 == k) + "\n"
        for k in range(5)
    ),
}
R_STEPS = {"detk-de": ("DESeq2",), "detk-enrich": ("fgsea",)}


def _quickstart_commands():
    text = (ROOT / "docs" / "quickstart.md").read_text()
    block = re.search(r"^```bash\n(.*?)^```", text, re.S | re.M).group(1)
    return [line for line in block.splitlines() if line.strip()]


def test_quickstart_runs_as_written(tmp_path):
    for name, text in QUICKSTART_DATA.items():
        (tmp_path / name).write_text(text)
    env = dict(os.environ, PATH=BIN_DIR + os.pathsep + os.environ.get("PATH", ""))
    skipped = []  # (line, what was missing)
    not_written = set()  # the files the left-out steps would have written
    for line in _quickstart_commands():
        argv = shlex.split(line)
        missing = missing_r(*R_STEPS[argv[0]]) if argv[0] in R_STEPS else None
        if missing is None and not_written.intersection(argv):
            missing = f"it reads {', '.join(sorted(not_written.intersection(argv)))}"
        if missing:
            skipped.append((line, missing))
            if "-o" in argv:
                not_written.add(argv[argv.index("-o") + 1])
            continue
        p = subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, text=True)
        assert p.returncode == 0, f"docs/quickstart.md: {line}\nexited {p.returncode}:\n{p.stderr}"
    filtered = (tmp_path / "raw_counts_filtered.csv").read_text().splitlines()
    # the filter keeps the rows with more than half their counts nonzero
    assert not any(line.startswith("g3,") for line in filtered)
    assert 1 < len(filtered) < 201
    assert (tmp_path / "detk_report" / "detk_report.html").is_file()
    if skipped:
        why = "; ".join(f"{line} ({missing})" for line, missing in skipped)
        if os.environ.get("DETK_TUTORIALS_REQUIRE_ALL"):
            pytest.fail(f"R or an R package is missing for: {why}")
        pytest.skip(f"quickstart steps not run: {why}")
