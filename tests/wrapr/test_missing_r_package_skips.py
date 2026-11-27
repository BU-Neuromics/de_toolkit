"""
With Rscript on PATH but DESeq2 and logistf missing from its library
(fgsea and jsonlite present), the tests that run DESeq2 or logistf skip,
naming the package, instead of failing (#187).

A stub Rscript stands in for that library, so this needs no R: it
answers `Rscript -e "library(pkg)"`, the check detk and the tests make,
and fails anything else. The six tests run in a pytest of their own with
the stub first on PATH.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

STUB = """#!/bin/sh
case "$2" in
  "library(fgsea)"|"library(jsonlite)") exit 0 ;;
  *) echo "Error: there is no package for: $2" >&2; exit 1 ;;
esac
"""

NEED_MISSING_PACKAGES = {
    "tests/cli/test_cli_help_sections.py::test_examples_run_where_test_data_allows[detk-de-deseq2]": "DESeq2",
    "tests/cli/test_cli_help_sections.py::test_examples_run_where_test_data_allows[detk-de-firth]": "logistf",
    "tests/cli/test_cli_help_sections.py::test_examples_run_where_test_data_allows[detk-transform-vst]": "DESeq2",
    "tests/cli/test_cli_help_sections.py::test_examples_run_where_test_data_allows[detk-transform-rlog]": "DESeq2",
    "tests/docs/test_docs_commands.py::test_quickstart_runs_as_written": "DESeq2",
    "tests/util/test_record.py::test_lineage_into_detk_de": "DESeq2",
}


@pytest.mark.skipif(os.name != "posix", reason="the stub Rscript is a shell script")
def test_tests_skip_naming_the_missing_r_package(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    (stub_dir / "Rscript").write_text(STUB)
    (stub_dir / "Rscript").chmod(0o755)
    env = dict(os.environ, PATH=str(stub_dir) + os.pathsep + os.environ.get("PATH", ""))
    env.pop("DETK_TUTORIALS_REQUIRE_ALL", None)  # set in the CI job with R
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", "-rs"]
        + [*NEED_MISSING_PACKAGES, "--basetemp", str(tmp_path / "run")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    out = p.stdout + p.stderr
    assert p.returncode == 0, out
    assert out.rstrip().splitlines()[-1].strip("= ").startswith("6 skipped"), out
    for package in set(NEED_MISSING_PACKAGES.values()):
        assert f"R package {package} is not installed" in out, out
    skips = [line for line in out.splitlines() if line.startswith("SKIPPED")]
    assert len(skips) >= 3 and all("is not installed" in line for line in skips), out
