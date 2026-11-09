---
kind: step
time: 2026-11-09T19:49:04Z
by: DETK/reviewer
node: release/gather
step: s2
branch: node/25-gather
verdict: changes
commits: []
decisions: []
---


# Review of #52: detk-util gather

## Summary

The implementation is careful and mostly right. Format detection works for
all four formats, including featureCounts without its comment line. Mixed and
unknown formats are refused with clear messages. `--column` works by name and
by position for every format. IDs and values pass through unchanged
(`0001`, `ENST00000456328.2`, `42.000`, `9.512`). Duplicate features,
non-numeric values (`NA`), duplicate sample names, a `--name-from` that does
not match or matches empty, and a quoted glob that matches nothing are all
errors. The `--on-mismatch` error message is clear (counts, which samples lack
how many, examples, what to do), and fill/drop behave as documented. The
report JSON and kv view are complete and escaped.

The output reads directly into `detk-filter`, `detk-norm deseq2|library` and
`detk-stats rowzero` with no changes, and leading zeros survive the round
trip. It handles 20 salmon samples x 250k transcripts in about 7 s and
0.7 GB. The quickstart's csvgather rule is replaced by an equivalent
`--name-from` and the csvgather link is gone. The CHANGELOG entry is good.

One defect blocks approval. The most common multi-sample htseq-count layout
silently loses samples (finding 1), which goes against the "must not guess
wrong silently" criterion in DETK-0012. The other findings are low or
informational.

DETK-0012 and DETK-0013 are sound. Recording them as Provisional for the
human is the right authority. `--on-mismatch` goes beyond the issue's
proposed usage, but the issue asks for "clear errors on feature-set
mismatches" and a report of "features dropped or filled", which implies a
fill and a drop path. The default `error` keeps the proposed usage
unchanged, so this is within what a developer may propose. One sentence of
DETK-0012's rationale is not accurate (finding 3).

## Artifacts

- Hands-on fixtures and outputs (salmon, kallisto, htseq, featureCounts,
  bad files, report, crate): scratchpad `rv52/`
- `uv sync`: ok
- `uv run pytest`: 224 passed, 49 skipped
- `ruff check`: passed; `ruff format --check`: 137 files already formatted
- `mkdocs build --strict`: built (the only notice is the Material team
  banner)
- `gh pr checks 52`: CodeQL, docs, ruff, tests on 3.10 to 3.13 passed;
  "test with R (bioconda)" still pending (gather has no R code)

## Findings

1. **medium** `de_toolkit/util.py:400` (`_DEFAULT_COLUMN["htseq"] = 1`) and
   `detect_format` at util.py:434. htseq-count 0.13 and later accept several
   BAMs and write one count column per sample (`ID<TAB>c1<TAB>c2...`).
   Detection accepts such a file as htseq because every field after the ID
   is an integer. Gather then extracts column 1 only and names the file as
   one sample. The other samples are dropped with no message: a 3-column
   htseq file gave a one-column matrix and exit code 0. Fix: either treat
   every column after the ID as a sample, as featureCounts does (names would
   need `--name-from` or a positional suffix, since htseq writes no header),
   or refuse a file with more than two columns unless `--column` is given.
   Add a test either way, and update the DETK-0012 "Default column" text to
   match.
2. **low** `de_toolkit/util.py:426` (`_is_number`). This uses `float()`,
   which accepts `nan`, `inf`, `Infinity`, `1_000` and padded `" 5"`. A
   salmon file with `nan`/`inf` NumReads gathered with exit code 0 and wrote
   `nan`/`inf` into the matrix. Docs util.md:60 say a value that is not a
   number is an error. Consider requiring a finite number, or record the
   behaviour.
3. **low** `.cogit/decisions/0012-...md:82` and `util.py:469`
   (`_default_names`). The decision says the default name "is the same for a
   file whichever others are gathered with it", and rejects option 3 for
   exactly that dependence. It is not true:
   - a single `sal/s1/quant.sf` is named `quant`, but with a second sample
     it is named `s1`;
   - two htseq `counts.txt` in different directories switch every sample to
     its directory name.

   The behaviour is reasonable. The rationale should say the fallback is
   all-or-nothing per run, and the docs should note that a lone `quant.sf`
   gives `quant`. The htseq default name keeps inner extensions
   (`A.counts.txt` becomes `A.counts`). This is documented but will usually
   need `--name-from`.
4. **low** `de_toolkit/util.py:716` and `crate.py`. In the RO-Crate the
   inputs appear only as one JSON-string PropertyValue
   (`"[\"ht/A.counts.txt\", ...]"`), with no input File entities. So the
   first step of a workflow has no provenance link to the quantifier
   outputs. This is a documented consequence in DETK-0012 (as for annotate,
   DETK-0007), and acceptable for this PR. Suggest a follow-up issue for
   multi-input modules in crate.py.
5. **info** `de_toolkit/util.py:686`. Glob expansion sorts
   lexicographically, so the column order is `s0,s1,s10,s11,...,s2`. This is
   harmless for detk tools, which match samples by name. Mention it in the
   docs or use natural sort.
6. **info** Scope. `de_toolkit/crate.py` (one SUBTOOLS line, needed for
   provenance) and `docs/quickstart.md` are outside the node's declared
   scope. Both are justified: the issue explicitly says gather "replaces the
   csvgather dependency in the quickstart docs". The plan's scope listed
   `docs/example.md`, which never used csvgather, instead of
   `docs/quickstart.md`. This is a plan-scope error, not a developer
   overreach. Everything else is in scope, apart from `.cogit/` records.
7. **info** `de_toolkit/report_specs.py` `build_gather`. In the report,
   `htseq_counters` lists only the samples that have each counter. When the
   samples differ (a file without `__ambiguous`), the view still lists the
   counter. Harmless.

## Questions

1. For multi-sample htseq files (finding 1), do you prefer one sample per
   count column (needs a naming rule, since htseq writes no header) or a
   refusal that asks for `--column`?
2. Should `nan`/`inf` be refused (finding 2)? A counts matrix should never
   hold them, but TPM gathering could arguably pass them through.
