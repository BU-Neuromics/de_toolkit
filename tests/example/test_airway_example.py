"""Integration test for the airway worked example (#16/#33).

Runs the real example pipeline (minus the network-dependent fgsea step) when
the required R packages are available; skips otherwise. This is the only test
that exercises the full documented workflow end to end.
"""

import os
import shutil
import subprocess
import sys

import pytest

EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "examples", "airway")


def _r_package_available(pkg):
    if shutil.which("Rscript") is None:
        return False
    p = subprocess.run(["Rscript", "-e", f"library({pkg})"], capture_output=True, text=True)
    return p.returncode == 0


requires_airway = pytest.mark.skipif(
    not (_r_package_available("airway") and _r_package_available("DESeq2")),
    reason="airway/DESeq2 R packages not available",
)


@requires_airway
def test_airway_example_runs(tmp_path):
    # stage the scripts into a scratch dir so generated files stay out of the repo
    for fn in ("run.sh", "prepare_data.R"):
        shutil.copy(os.path.join(EXAMPLE_DIR, fn), tmp_path)

    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    p = subprocess.run(
        ["bash", "run.sh", "--skip-enrich"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    assert p.returncode == 0, f"stdout:\n{p.stdout[-3000:]}\nstderr:\n{p.stderr[-3000:]}"

    report = tmp_path / "detk_report" / "detk_report.html"
    assert report.exists()
    html = report.read_text()
    # every family the pipeline touches must be present in the report
    for module in (
        "basestats",
        "pca",
        "filtercounts",
        "deseq2norm",
        "vstcounts",
        "entropycounts",
        "deseq2counts",
    ):
        assert module in html, f"{module} missing from the example report"
    assert (tmp_path / "ro-crate-metadata.json").exists()
