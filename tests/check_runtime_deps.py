"""Check that detk runs on its runtime dependencies alone (DETK-0001, DETK-0026).

statsmodels is a test-only dependency (DETK-0026), and patsy and docopt-ng
were removed from the runtime dependencies when detk moved to formulaic and
argparse (DETK-0001); patsy still comes into the dev environment through
statsmodels. None of them may be installed with detk's runtime dependencies,
and no module of de_toolkit may import them. CI runs this script in an
environment with only the runtime dependencies installed (`uv sync --locked
--no-dev`), so a runtime dependency on any of them, or a runtime use of
them, fails here instead of reaching users.

Run it as a plain script, not through pytest (pytest is not a runtime
dependency):

    uv run --no-dev python tests/check_runtime_deps.py

The file name does not match pytest's test_*.py pattern, so the test suite
does not collect it.
"""

import importlib
import importlib.util
import pkgutil
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# packages that must not be installed with detk's runtime dependencies, by
# import name: the package each one comes from
TEST_ONLY = {
    "statsmodels": "statsmodels",
    "patsy": "patsy",
    "docopt": "docopt-ng",
}


def main():
    for name, package in TEST_ONLY.items():
        if importlib.util.find_spec(name) is not None:
            sys.exit(
                f"{package} is installed: run this check in an environment with "
                "only detk's runtime dependencies (uv sync --locked --no-dev)"
            )

    import de_toolkit

    modules = ["de_toolkit"] + [
        m.name for m in pkgutil.walk_packages(de_toolkit.__path__, prefix="de_toolkit.")
    ]
    for name in modules:
        importlib.import_module(name)
        print(f"imported {name}")

    # run a detk command end to end on a small counts file
    detk_norm = shutil.which("detk-norm")
    if detk_norm is None:
        sys.exit("detk-norm is not on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        counts = tmp / "counts.csv"
        counts.write_text("gene,a,b,c\ng1,10,20,30\ng2,5,0,15\ng3,85,80,55\n")
        out = tmp / "cpm.csv"
        subprocess.run([detk_norm, "cpm", "-o", str(out), str(counts)], check=True, cwd=tmp)
        lines = out.read_text().splitlines()
        if len(lines) != 4:
            sys.exit(f"detk-norm cpm wrote {len(lines)} lines, expected 4:\n{out.read_text()}")
        print(f"ran detk-norm cpm: {len(lines) - 1} features")

    print(
        f"{len(modules)} modules import and detk-norm runs without {', '.join(TEST_ONLY.values())}"
    )


if __name__ == "__main__":
    main()
