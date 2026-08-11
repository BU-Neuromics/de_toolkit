# Quickstart

`detk` implements the common operations when working with count matrices from
high-throughput sequencing experiments. The following diagram illustrates a
simple RNA-seq workflow downstream of quantification:

![simple pipeline](simple_pipeline.png)

This workflow performs the following, all without any custom code:

1. Takes the output from read counting (e.g. [htseq-count]) or expression
   estimation software (e.g. [salmon] or [kallisto]) and combines them into a
   single counts matrix using the [csvgather] tool
2. Calculates statistics on the zero-ness of genes to guide feature filtering
   with [`detk-stats rowzero`](tools/stats.md#rowzero)
3. Filters out rows with half or more zero counts with
   [`detk-filter`](tools/filter.md)
4. Normalizes the filtered matrix with the DESeq2 procedure via
   [`detk-norm deseq2`](tools/norm.md#deseq2)
5. Computes principal components on the normalized matrix to identify outlier
   samples with [`detk-stats pca`](tools/stats.md#pca)
6. Removes a hypothetical outlier sample with `csvcut` from [csvkit]
7. Runs DESeq2 differential expression with
   [`detk-de deseq2`](tools/de.md#deseq2)
8. Computes pre-ranked GSEA on the DE statistics with
   [`detk-enrich fgsea`](tools/enrich.md)

On the command line, the core of that workflow is:

```bash
detk-stats rowzero -o raw_counts_rowzero_stats.csv raw_counts.csv
detk-filter "nonzero(all) < 0.5" -o raw_counts_filtered.csv raw_counts.csv
detk-norm deseq2 -o norm_counts_filtered.csv raw_counts_filtered.csv
detk-stats pca -o norm_counts_filtered_pca.csv norm_counts_filtered.csv
detk-de deseq2 -o deseq2_results.csv "counts ~ cond" raw_counts_filtered.csv sample_info.csv
detk-enrich fgsea -o gsea_results.csv -i gene -c cond__log2FoldChange msigdb_c2cp.gmt deseq2_results.csv
detk-report generate
```

The final command renders every step's recorded JSON into a single
self-contained HTML [report](report.md).

## Using a workflow manager

detk tools are plain command-line filters, which makes them trivial to embed
in whichever workflow manager you already use. The same workflow in
[Snakemake]:

```python
from glob import glob

rule all:
    input:
        'detk_report/detk_report.html',
        'msigdb_c2cp_gsea_results.csv'

rule gather_counts:
    input: glob('sample_*__salmon_counts/quant.sf')
    output: 'raw_counts.csv'
    shell:
        '''
        csvgather -j 0 -f NumReads -f "s:NumReads:{{dir}}:" \
            -f "s:__salmon_counts::" -o {output} \
            {input}
        '''

rule raw_rowzero:
    input: 'raw_counts.csv'
    output: 'raw_counts_rowzero_stats.csv'
    shell:
        'detk-stats rowzero -o {output} {input}'

rule filter_raw:
    input: 'raw_counts.csv'
    output: 'raw_counts_filtered.csv'
    shell:
        'detk-filter "nonzero(all) < 0.5" -o {output} {input}'

rule deseq2_norm:
    input: 'raw_counts_filtered.csv'
    output: 'norm_counts_filtered.csv'
    shell:
        'detk-norm deseq2 -o {output} {input}'

rule pca:
    input: 'norm_counts_filtered.csv'
    output: 'norm_counts_filtered_pca.csv'
    shell:
        'detk-stats pca -o {output} {input}'

rule de:
    input:
        counts='raw_counts_filtered.csv',
        covs='sample_info.csv'
    output: 'deseq2_results.csv'
    shell:
        'detk-de deseq2 -o {output} "counts ~ cond" {input.counts} {input.covs}'

rule gsea:
    input:
        de='deseq2_results.csv',
        gmt='msigdb_c2cp.gmt'
    output: 'msigdb_c2cp_gsea_results.csv'
    shell:
        'detk-enrich fgsea -o {output} -i gene -c cond__log2FoldChange {input.gmt} {input.de}'

rule generate_detk_report:
    input:
        rules.raw_rowzero.output,
        rules.pca.output,
        rules.de.output
    output: 'detk_report/detk_report.html'
    shell:
        'detk-report generate'
```

Run with `snakemake --cores 1`. A [Nextflow] process wrapping any of these
commands looks the same: detk needs nothing from the workflow manager beyond a
shell.

[htseq-count]: https://htseq.readthedocs.io
[salmon]: https://combine-lab.github.io/salmon/
[kallisto]: https://pachterlab.github.io/kallisto/
[csvgather]: https://bitbucket.org/adamlabadorf/csvgather/
[csvkit]: https://csvkit.readthedocs.io
[Snakemake]: https://snakemake.readthedocs.io/en/stable/
[Nextflow]: https://www.nextflow.io/
