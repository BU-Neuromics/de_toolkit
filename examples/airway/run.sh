#!/usr/bin/env bash
# Regenerate the detk example report from the airway RNA-seq dataset
# (GEO GSE52778). Requires: detk installed, R with the airway, org.Hs.eg.db,
# DESeq2 and fgsea Bioconductor packages on PATH.
#
# Usage:
#   ./run.sh [--skip-enrich] [--publish]
#
#   --skip-enrich  skip the fgsea step (no network / GMT download needed)
#   --publish      copy the finished report + provenance crate into
#                  ../../docs/example/ for the documentation site
set -euo pipefail
cd "$(dirname "$0")"

SKIP_ENRICH=0
PUBLISH=0
for arg in "$@"; do
    case "$arg" in
        --skip-enrich) SKIP_ENRICH=1 ;;
        --publish) PUBLISH=1 ;;
        *) echo "unknown argument: $arg" >&2; exit 2 ;;
    esac
done

echo "== preparing airway data (Bioconductor airway package)"
Rscript prepare_data.R

echo "== stats on the raw counts"
detk-stats summary --log --color-col=dex -o raw_summary_stats.csv counts.csv sample_info.csv

echo "== filtering: keep genes with nonzero counts in at least half the samples"
detk-filter 'nonzero(all) >= 0.5' -o counts_filtered.csv counts.csv

echo "== DESeq2 normalization"
detk-norm deseq2 -o norm_counts.csv --size-factors=size_factors.tsv counts_filtered.csv

echo "== variance-stabilizing transform"
detk-transform vst -o vst_counts.csv counts_filtered.csv

echo "== entropy-based outlier flagging"
detk-outlier entropy counts_filtered.csv -p 0.05 -o entropy_flags.csv

echo "== DESeq2 differential expression: counts ~ cell + dex[untrt]"
detk-de deseq2 -o deseq2_results.csv "counts ~ cell + dex[untrt]" counts_filtered.csv sample_info.csv

if [ "$SKIP_ENRICH" -eq 0 ]; then
    echo "== gene set enrichment against WikiPathways (CC0)"
    # WikiPathways GMTs are keyed by Entrez gene ID; join IDs onto the results
    # (use the python detk runs under, which is guaranteed to have pandas)
    DETK_PY="$(dirname "$(command -v detk-de)")/python3"
    [ -x "$DETK_PY" ] || DETK_PY=python3
    "$DETK_PY" - <<'PY'
import pandas as pd
res = pd.read_csv("deseq2_results.csv")
gene_col = res.columns[0]
gmap = pd.read_csv("gene_map.csv", dtype=str)
res = res.merge(gmap[["gene", "entrez"]], left_on=gene_col, right_on="gene", how="left")
res = res.dropna(subset=["entrez"]).drop_duplicates(subset=["entrez"])
res.to_csv("deseq2_results_entrez.csv", index=False)
print(f"kept {len(res)} genes with Entrez IDs")
PY
    if [ ! -f wikipathways.gmt ]; then
        GMT_NAME=$(curl -fsSL https://data.wikipathways.org/current/gmt/ \
            | grep -o 'wikipathways-[0-9]*-gmt-Homo_sapiens.gmt' | head -1)
        echo "   downloading $GMT_NAME"
        curl -fsSL "https://data.wikipathways.org/current/gmt/${GMT_NAME}" -o wikipathways.gmt
    fi
    detk-enrich fgsea --filter-unannotated -i entrez -c 'dex__trt__log2FoldChange' \
        -o fgsea_results.csv wikipathways.gmt deseq2_results_entrez.csv
else
    echo "== skipping enrichment (--skip-enrich)"
fi

echo "== generating the report"
detk-report generate

echo "report: $(pwd)/detk_report/detk_report.html"
echo "provenance: $(pwd)/ro-crate-metadata.json"

if [ "$PUBLISH" -eq 1 ]; then
    echo "== publishing into docs/example/"
    mkdir -p ../../docs/example
    cp detk_report/detk_report.html ../../docs/example/detk_report.html
    cp ro-crate-metadata.json ../../docs/example/ro-crate-metadata.json
fi
