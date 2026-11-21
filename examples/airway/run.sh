#!/usr/bin/env bash
# Regenerate the published example report (docs/example/) from the airway
# tutorial, docs/tutorials/airway.md: run the page as its test runs it, then
# copy the report and the provenance crate the run made into docs/example/.
# The commands live on the page only (DETK-0064); this script runs nothing
# else.
#
# Requires: uv, and R on PATH with DESeq2, airway and org.Hs.eg.db (see the
# tutorial). Usage, from anywhere in the repository:
#
#   examples/airway/run.sh
#
# The run's working directory is left in examples/airway/run/airway0/.
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
run="$repo/examples/airway/run"
cd "$repo"

DETK_TUTORIALS_REQUIRE_ALL=1 uv run pytest tests/tutorials/test_tutorials.py \
    -k airway -o addopts="" -p no:cacheprovider --basetemp="$run"

mkdir -p docs/example
cp "$run/airway0/detk_report/detk_report.html" docs/example/detk_report.html
cp "$run/airway0/ro-crate-metadata.json" docs/example/ro-crate-metadata.json
echo "published: docs/example/detk_report.html, docs/example/ro-crate-metadata.json"
