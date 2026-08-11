#!/usr/bin/env Rscript
# Extract the airway dataset (GEO GSE52778; Himes et al. 2014, PMID 24926665)
# into the plain files detk consumes:
#
#   counts.csv      gene-level counts, Ensembl gene IDs x 8 samples
#   sample_info.csv column data: cell line and dexamethasone treatment
#   gene_map.csv    Ensembl -> Entrez / symbol mapping (for gene set analysis)
#
# The airway Bioconductor data package redistributes the published counts;
# see https://bioconductor.org/packages/airway/ for provenance.

suppressMessages({
    library(airway)
    library(org.Hs.eg.db)
})

data(airway)

counts <- as.data.frame(assay(airway))
counts <- cbind(gene = rownames(counts), counts)
write.csv(counts, "counts.csv", row.names = FALSE, quote = FALSE)

cd <- as.data.frame(colData(airway)[, c("cell", "dex")])
cd <- cbind(sample = rownames(cd), cd)
write.csv(cd, "sample_info.csv", row.names = FALSE, quote = FALSE)

# mapping for downstream gene set enrichment (WikiPathways GMTs use Entrez)
ens <- rownames(assay(airway))
entrez <- mapIds(org.Hs.eg.db, keys = ens, column = "ENTREZID",
                 keytype = "ENSEMBL", multiVals = "first")
symbol <- mapIds(org.Hs.eg.db, keys = ens, column = "SYMBOL",
                 keytype = "ENSEMBL", multiVals = "first")
map <- data.frame(gene = ens, entrez = unname(entrez), symbol = unname(symbol))
write.csv(map, "gene_map.csv", row.names = FALSE, quote = FALSE)

cat(sprintf("wrote counts.csv (%d genes x %d samples), sample_info.csv, gene_map.csv\n",
            nrow(counts), ncol(counts) - 1))
