---
kind: step
time: 2026-11-09T18:38:30Z
by: DETK/reviewer
node: release/agent-skills
step: s2
branch: node/38-agent-skills
verdict: changes
commits: []
decisions: []
---


# Review of PR #42: the detk agent skill

## Summary

The skill is laid out the way `npx skills` expects, installs cleanly, and is mostly accurate. Every command, subcommand and option it names exists in the CLI. The filter direction is stated correctly (the expression describes the rows to keep). The formula syntax (`counts ~ cell + dex[untrt]`, `condition[control] ~ counts` for Firth) and the `dex__trt__<stat>` column names match patsy_lite and the R code in `de.py`. I ran the pure-Python half of the airway pipeline from a fresh directory, following `references/airway.md`. Filter, DESeq2 normalization, stats, entropy and the report all ran. The filter kept 24,706 genes, which matches the skill's "about 24,700". The size factors match DESeq2's known airway values.

Three things need changing before acceptance:

- The first instruction, `pip install de_toolkit`, installs a version that cannot run.
- The skill relies on `--size-factors=FILE`, which detk silently ignores.
- The skill recommends `detk-norm library`, which crashes.

The second and third are bugs in the CLI, not in this PR, but the skill sends an agent straight into them. The drift test works for what it covers, but it covers less than DETK-0010 and the docs page say it does.

## Artifacts

- Worktree `node/38-agent-skills` at f03f4cb; PR BU-Neuromics/de_toolkit#42.
- Checks: `uv run pytest` 156 passed, 49 skipped. `uv run ruff check .` clean. `uv run --group docs mkdocs build --strict` clean.
- `gh pr checks 42`: docs build, test (python 3.10) and CodeQL analyze all pass. "test with R (bioconda)" was still running when this review was recorded. That job runs `examples/airway/run.sh --skip-enrich`, i.e. the same DESeq2 commands as the skill's airway reference.
- Install check: I ran `npx --yes skills add 'BU-Neuromics/de_toolkit#node/38-agent-skills' -a claude-code -y` in a fresh git directory, with HOME and XDG_* pointed at an empty scratch directory and DISABLE_TELEMETRY=1. The result:
  - It installed `.claude/skills/detk/{SKILL.md,references/airway.md,references/commands.md}`, byte-identical to `skills/detk/`.
  - It wrote `skills-lock.json` (source BU-Neuromics/de_toolkit, ref node/38-agent-skills, skillPath skills/detk/SKILL.md).
  - Nothing landed in the scratch home except the npm cache, and the real home was untouched.
- Airway run, without R: `/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/review42/airway-run/`
  - Inputs: `counts.csv` (63,677 × 8) and `sample_info.csv` (sample, cell, dex). I extracted them from the Bioconductor `airway_1.32.0` tarball's `airway.RData` with the pure-Python `rdata` package, in the same layout `prepare_data.R` writes. No gene map, because org.Hs.eg.db needs R.
  - detk installed by the skill's GitHub fallback.
  - Ran and succeeded:
    - `detk-stats summary --log --color-col=dex`
    - `detk-filter 'nonzero(all) >= 0.5'` (24,706 kept)
    - `detk-norm deseq2` (size factors 1.024, 0.896, 1.179, 0.670, 1.178, 1.399, 0.921, 0.945)
    - `detk-outlier entropy -p 0.05`
    - `detk-report generate` (9 modules, crate written)
  - Failed cleanly with "Rscript executable not found" and exit 1, as expected: `detk-transform vst`, `detk-de deseq2`, `detk-wrapr check`. `detk-enrich fgsea` was not attempted.
- I also checked the other filter forms SKILL.md gives, on airway: `mean(all) > 10` kept 16,055; `mean(all) > 10 and zero(all) < 0.5` kept 16,047; `nonzero(dex) > 0.5` kept 24,270. All parse and behave as described.
- Mutation test of `tests/skills/test_skills.py`, run on copies in scratch (baseline 8 passed):
  - Caught: a bogus option in a bash block; a wrong subcommand in a bash block.
  - Missed: a renamed option in prose (`--last-term-onlyx`); a wrong subcommand in prose (`detk-norm libary`); `detk-de deseq2` missing its `<cov_fn>`; a misspelled option inside a block fenced `sh` instead of `bash`.

## Findings

1. **`skills/detk/SKILL.md:25-34`: the primary install line installs a detk that cannot start.** Severity: major.
   - `pip install de_toolkit` gets 0.9.12 from PyPI. On Python 3.10 or newer (the skill's stated minimum) every command dies on import with `ImportError: cannot import name 'Mapping' from 'collections'`. I checked this in a clean venv.
   - The skill's fallback condition, "if the installed version has no `detk-report generate`", does not describe that failure. An agent seeing a traceback is as likely to downgrade Python or patch site-packages as to reinstall from GitHub.
   - Checking the version cannot help either: the GitHub build also reports `detk version: 0.9.12`, because the release is not cut yet.
   - This blocks the acceptance item: the first step of the airway run fails today.
   - Fix: lead with `pip install 'de_toolkit>=1.0'`, and if pip finds no such version, use `pip install git+https://github.com/BU-Neuromics/de_toolkit.git` (that fallback works; I checked). Name the ImportError as the sign of the stale release.

2. **`skills/detk/SKILL.md:114-118` and `references/airway.md:66-67`: `--size-factors=size_factors.tsv` writes nothing.** Severity: medium.
   - The option is in `detk-norm deseq2`'s usage, but `de_toolkit/norm.py` never reads `args["--size-factors"]`. No file appears, there is no warning, and the exit code is 0. This holds on this branch and on main.
   - The skill says it is "writing the size factors for the report". In fact the report already gets the size factors from the module's JSON properties, so the option does nothing.
   - An agent following step 4 ("paths to the result tables") will report, or go looking for, a file that does not exist.
   - Fix: drop the option from the skill and say the size factors are in the report. Separately, file an issue for the CLI bug, which is out of this node's scope. `docs/example.md:56` and `examples/airway/run.sh:35` carry the same dead option.

3. **`skills/detk/SKILL.md:121`: `detk-norm library` is recommended but crashes on every input.** Severity: medium.
   - It fails with `ERROR: 'CountMatrixFile' object has no attribute 'sum'` and exit 1, on this branch, on main and on airway.
   - This is a CLI bug from before this PR, and the drift test cannot see it.
   - Fix: remove the recommendation until the command is fixed (#24 touches `norm.py` and may be the place to fix it), and file an issue.

4. **`tests/skills/test_skills.py:40-48, 97-102`, with `.cogit/decisions/0010-…md` (Decision and Consequences) and `docs/agent-skills.md:79-81`: the drift test checks less than it is said to.** Severity: medium.
   - What it catches: a renamed or removed command, subcommand or option in a ```` ```bash ```` line, and a usage line copied into `commands.md` that no longer appears in `--help`. Both confirmed by mutation.
   - What it misses (confirmed by mutation):
     - Commands and options in inline prose. SKILL.md names `detk-norm library`, `--last-term-only`, `--filter-unannotated`, `--report-dir=DIR`, `-i` and `-c` only in prose.
     - Positional arity. Dropping `<cov_fn>` from `detk-de deseq2` passes.
     - Blocks fenced with another language.
   - Option matching is a regex anywhere in the help text, so an option named only in a description line would also pass.
   - DETK-0010 says the test "checks both the prose command lines and the copied usage" and that it checks "only that it parses". Neither is accurate: it does not parse, and it does not check prose. The docs page says it checks "every `detk-*` command line in the skill".
   - Fix: parse each bash command with docopt against the module's usage, which catches arity and mis-ordered options, and check inline `` `detk-…` `` / `` `--opt` `` spans against the nearest command. Or narrow the claims in DETK-0010 and the docs page to what the test does.

5. **`skills/detk/SKILL.md:101-112`: filter thresholds can be read two ways.** Severity: low.
   - For `zero` and `nonzero`, a threshold strictly between 0 and 1 is a fraction of samples; 0 or anything ≥ 1 is a count of samples (`docs/tools/filter.md:39`). The skill does not say this.
   - An agent writing `nonzero(all) >= 1` to mean "nonzero in every sample" keeps genes nonzero in at least one sample: 33,469 on airway, against 24,706 for `>= 0.5`.
   - The single-group form `nonzero(dex[trt]) >= 0.5` is not mentioned.
   - The single-letter column names the lexer rejects (`t_WORD` needs two or more characters) are worth one line too.

6. **`skills/detk/references/airway.md:88`: the Ensembl-to-Entrez join may run in a Python without pandas.** Severity: low.
   - It runs `python - <<'PY'` and imports pandas. SKILL.md:26 suggests `uv tool install de_toolkit`, and under that (or pipx) the `python` on PATH need not have pandas.
   - `examples/airway/run.sh` uses detk's own interpreter for exactly this reason.
   - Fix: say so, or use the same `$(dirname $(command -v detk-de))/python3` approach.

7. **`skills/detk/SKILL.md:152-161` and `references/airway.md:103`: the fgsea ranking statistic is open to question.** Severity: low (statistics).
   - Both rank by the unshrunk `__log2FoldChange`. With unshrunk DESeq2 fold changes, noisy low-count genes sit at the extremes. The Wald `__stat` column is the more usual preranked-GSEA statistic.
   - This matches the published example, so it is a question rather than an error.
   - The skill should also warn that omitting `-c` ranks by the last numeric column. On detk DESeq2 output that is the last term's `__padj`, so the ranking is backwards and on the wrong quantity.

8. **`skills/detk/SKILL.md:144-150, 181-187`: the Firth path does not give its output column names.** Severity: low.
   - The report-back step only tells the agent DESeq2 column names. Firth results are `<term>__beta`, `<term>__p`, `<term>__padj` (for example `counts__padj`), plus a `status` column.
   - Separately, `ro-crate-metadata.json` is written in the working directory, not under `detk_report/`. Saying so would stop an agent looking in the wrong place.

What I checked and found correct:

- Every option and subcommand named in bash blocks, and every usage block in `commands.md`, against `--help` and the docopt strings.
- Filter keep-semantics and the "kept if any group passes" union for grouped clauses.
- The `--last-term-only` description, and the absence of Cook's distance and independent filtering (the R code uses plain `p.adjust(..., 'fdr')`).
- The `features kept after filtering` log line.
- `detk-wrapr check` exits 1 without R.
- CHANGELOG entry under 1.0.0 Added; mkdocs nav; README section.
- No existing file outside the node's scope is changed. README, mkdocs.yml and CHANGELOG get added rows only; skills/, docs/agent-skills.md and tests/skills/ are new files.
- DETK-0009's reasoning (one skill plus references, under `skills/`) holds, and its install line works.

## Questions

1. The R half of the airway run is NOT verified by this review: `detk-transform vst`, `detk-de deseq2` (`counts ~ cell + dex[untrt]`, the `dex__trt__*` columns), the Ensembl-to-Entrez join, `detk-enrich fgsea` against WikiPathways, and the final report with DE and enrichment views. R is not installed on this machine. That falls to Adam: run the skill from a fresh project with R. The "test with R (bioconda)" CI job, still running at review time, covers the DESeq2 part through `run.sh`, but not through the skill and not fgsea.
2. Should the CLI bugs from findings 2 and 3 be filed as issues now, and should #24 (tpm-cpm, which edits `norm.py`) take the `detk-norm library` fix?
3. `detk-util tidy -p` writes a sample table with an extra `counts` column of zeros (seen on airway). Is that intended? If not, the skill's tidy step passes it to the agent, and it may confuse a design that names `counts`.
4. Ranking statistic for fgsea (finding 7): keep `log2FoldChange` to match the published example, or move both to `stat`? That is Adam's call, and would be a Proposed decision if it changes the example.
