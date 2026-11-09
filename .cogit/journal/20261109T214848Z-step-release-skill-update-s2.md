---
kind: step
time: 2026-11-09T21:48:48Z
by: DETK/reviewer
node: release/skill-update
step: s2
branch: node/62-skill-update
verdict: approve
commits: []
decisions: []
---


# Review of #64: bring the detk agent skill up to date for 1.0

## Summary

Reviewed ee582ea (node/62-skill-update) against freshly fetched origin/main,
reading `skills/detk/` cold as an agent would.

Acceptance:

1. Met. SKILL.md and `references/commands.md` name `detk-util gather`,
   `detk-util annotate`, `detk-norm cpm`, `tpm` and `library`. Every usage
   block matches `uv run <cmd> --help` line for line, and every command line
   parses with docopt. tests/skills: 19 passed.
2. Met. Section 2, "Starting from quantifier outputs", leads with gather for
   salmon, kallisto, htseq and featureCounts. Keeping airway as a counts
   matrix is right: the airway Bioconductor package ships only a
   SummarizedExperiment of counts, with no per-sample quantifier files, so
   gather cannot be shown on it. airway.md says so and points to the gather
   section.
3. Met (this point is not yet in the node file). The warning against
   `detk-norm library` is gone. library is listed with deseq2, cpm, tpm and
   fpkm, each with when to use it.

The statistics are sound:
- deseq2 is for comparing a gene between samples, and its size factors
  resist composition effects.
- CPM is simple and suffers composition bias; the skill says so.
- library is CPM without the 1e6 factor.
- TPM is length then depth, for comparing genes within a sample.
- The FPKM formula matches the code and the CHANGELOG. "0.9.x never divided
  by library size" is true; 0.9.x also had the wrong length factor, but the
  advice not to compare old and new values holds either way.
- "Do not pass normalized counts to detk-de deseq2" is kept.

The zero-padded ID claim matches CHANGELOG/DETK-0015. I checked that `007`
survives tidy, filter, norm, stats and annotate. All findings are low
severity.

## Artifacts

All under /tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/rv64/

- `checks.txt`: pytest, ruff, mkdocs and `gh pr checks`.
- `toy1/`: the skill's four gather lines on toy salmon (`quant.sf` and
  `quant.genes.sf`), htseq and featureCounts files.
  - Names came out A,B,s2,s10 with `--name-from` and the quoted glob, and
    A_quant... without `--name-from`.
  - htseq `__*` lines were dropped and recorded in the report JSON.
  - featureCounts columns were named f1 and f2.
- `toy2/`, `toy3/`: tidy, filter, stats, and all five norm methods with a
  lengths file. annotate used a toy mapping that includes padded IDs. It
  logged "features mapped: 2 of 3" plus a warning about the unmapped ID.
- `toy4/`: a gather feature mismatch stops with the error the skill
  describes.
- `airway/`: the non-R airway steps by airway.md, on the counts from
  review42:
  - `detk-stats summary`, filter (kept 24706, matching "about 24,700"),
    `detk-norm deseq2`, `detk-outlier entropy`, `detk-report generate`.
  - annotate `--map-to=symbol` on a stand-in results table (R is absent)
    with a synthetic map: unmapped rows got an empty symbol, and
    `num_unmapped` went into the report.
  - annotate `--map-to=entrez` produced 12103 duplicate Entrez IDs, which
    confirms why airway.md keeps its dedup join for fgsea.
- `mut/mutate.py`: mutation test of the drift checker on copies of the three
  files. 17 of 17 meaningful mutations were caught:
  - block option, missing and extra positional;
  - prose subcommand typos for gather, cpm and library;
  - option typos in prose for `--on-mismatch`, `--map-from`,
    `--strip-versions`, `--drop-unmapped` and `--name-from`;
  - an option attributed to the wrong command;
  - commands.md usage edits to the gather, tpm and annotate usage;
  - the airway annotate block.
  
  3 known limits were missed: positionals in a prose span (finding 4),
  option values (`--on-mismatch=sum`), and column names in prose.
- `install/`: `npx --yes skills add 'BU-Neuromics/de_toolkit#node/62-skill-update' -a claude-code -y`
  with HOME/XDG_* pointed at an empty scratch dir and DISABLE_TELEMETRY=1. It
  installed `./.claude/skills/detk` (copied), and `diff -r` shows it is
  identical to `skills/detk` at ee582ea.
- Checks:
  - `uv run pytest`: 306 passed, 49 skipped (the R-gated tests).
  - `ruff check`: clean; `ruff format --check`: clean.
  - `mkdocs build --strict`: built.
  - `gh pr checks 64`: all pass except "test with R (bioconda)", which was
    still pending at review time.

Unverified because R is not installed (that stays Adam's):
- `detk-de deseq2` and `firth`, `detk-transform vst` and `rlog`,
  `detk-enrich fgsea`, `detk-wrapr check`, airway step 1 (`prepare_data.R`),
  and annotate on real DESeq2 output.
- That R turns `007` into `7`: taken from DETK-0015 and code reading
  (`read.csv` without colClasses).
- That `detk-de deseq2` rounds salmon/kallisto fractions: checked by reading
  de.py:263-266 only.

## Findings

1. skills/detk/SKILL.md:69, low. The list of commands that "work without R"
   names `detk-stats`, `detk-filter`, `detk-norm`, `detk-report` but not
   `detk-util` (gather, tidy, annotate) or `detk-outlier`. Read literally, an
   agent without R might skip gather or annotate. Add `detk-util` and
   `detk-outlier`.
2. skills/detk/SKILL.md:84-89, low. The padded-ID sentence sorts commands
   into Python and R-backed but leaves out `detk-enrich fgsea`. It reads the
   result table with plain `pandas.read_csv` (de_toolkit/enrich.py:386, no
   `dtype=str`), so an all-numeric ID column such as `007` would reach fgsea
   as `7`. This is from code reading, not run. Entrez and symbols are rarely
   padded, so the practical impact is small. Name fgsea among the commands
   that do not keep padding yet.
3. skills/detk/SKILL.md:106-108, low. The skill says names come "from the
   file names without their last extension, or, when those are all the same
   ..., from each file's directory". `--help` says "when those are not unique
   among the files given" (any repeat switches every file to its directory).
   A single `quant.sf` is named `quant`, not after its directory (verified:
   toy1/counts4.csv header is `,quant`). An agent gathering one salmon
   sample would get a wrong name. Match the help wording and mention the
   single-file case, or say to pass `--name-from`.
4. skills/detk/SKILL.md:199-200, low. The only TPM command line is an inline
   span. The drift test does not check positionals in prose: the mutation
   that drops `lengths.csv` passed. Put it in a bash block, as fpkm and the
   others are in airway.md.
5. skills/detk/SKILL.md:189-192 with :200, low, statistical. CPM is offered
   "for expression thresholds", but the skill's flow and its TPM example
   normalize `counts_filtered.csv`, so "per million" is relative to the kept
   features. CPM thresholds (as in edgeR's filterByExpr) are normally taken
   on the full library, before filtering. The effect is small after a
   nonzero filter, but one clause would help: compute CPM on the unfiltered
   counts when it is used to choose a filter, and expect TPM from the
   filtered matrix not to match salmon's own TPM column.
6. skills/detk/SKILL.md:128-129, low, unverified (needs R). "`detk-de deseq2`
   rounds them" is true (de.py:263). `detk-transform vst`, used in
   airway.md:76, does not round: the effective `VstCounts` at
   de_toolkit/transform.py:168-180 passes `read.csv` values straight to
   `DESeqDataSetFromMatrix`, which refuses non-integers. Only rlog rounds
   (transform.py:246). vst on gathered salmon or kallisto counts is
   therefore likely to fail. Either say only deseq2 and rlog round, or open
   an issue to round in vst.
7. tests/skills/test_skills.py, low (suggestion). Nothing checks that every
   command used in SKILL.md has a `## \`detk-x sub\`` section in
   commands.md. Acceptance 1 holds by inspection, but a later command could
   be added to SKILL.md without its usage. A short completeness test would
   enforce it.

## Questions

- Pre-existing, outside this PR: `detk-util tidy -p` writes the sample info
  with an empty index header and an extra `counts` column of zeros
  (de_toolkit/util.py:790, the count object's column data; see
  toy3/st.csv). The skill tells agents to use that file as the sample info
  for `detk-de`. Is that intended, or worth an issue? Whether `detk-de
  deseq2` accepts it is unverified without R.
- The `test with R (bioconda)` CI job was pending at review time. Adam,
  please confirm it is green before s3.
