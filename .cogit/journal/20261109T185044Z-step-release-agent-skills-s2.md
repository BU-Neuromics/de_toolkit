---
kind: step
time: 2026-11-09T18:50:44Z
by: DETK/reviewer
node: release/agent-skills
step: s2
branch: node/38-agent-skills
verdict: approve
commits: []
decisions: []
---


# Re-review of PR #42: the detk agent skill

## Summary

All eight findings from the earlier s2 review are fixed, and I checked each one against the code and by running it.

- **Install:** the skill now leads with `pip install 'de_toolkit>=1.0'`. In a fresh venv that finds no match today, and the GitHub fallback the skill gives next installs a working detk. The skill names the `Mapping` ImportError as the sign of the stale 0.9.12 release.
- **Dead and crashing commands:** the skill no longer passes the ignored `--size-factors`. It now tells the agent not to use `detk-norm library`, which still crashes.
- **Drift test:** it now parses every command line in a block with docopt, and checks commands and options named in prose. Twenty of my 27 mutations were caught. The seven it missed fall outside the documented scope or are minor gaps, listed in finding 2.
- **Low findings:** the filter thresholds, the single-group filter form, the Firth columns, the interpreter for the Entrez join, the crate location and the fgsea `-c` warning are all addressed. I confirmed the filter semantics on airway.

What remains is low severity and does not block acceptance. The R half of the airway run is not verified here (see Questions).

## Artifacts

- PR BU-Neuromics/de_toolkit#42. Branch `node/38-agent-skills` at 9514c5a, diffed against `origin/main`.
- **Checks:**
  - `uv run pytest`: 167 passed, 49 skipped.
  - `uv run ruff check .`: clean.
  - `uv run ruff format --check .`: 116 files already formatted.
  - `uv run --group docs mkdocs build --strict`: clean.
  - `gh pr checks 42`: CodeQL, docs build (strict), ruff and test on Python 3.10 to 3.13 all pass. "test with R (bioconda)" was still pending when this was recorded.
- **Install check:**
  - Ran `npx --yes skills add 'BU-Neuromics/de_toolkit#node/38-agent-skills' -a claude-code -y` in a fresh `git init` directory, with HOME and XDG_* pointed at an empty scratch dir and DISABLE_TELEMETRY=1.
  - It installed `.claude/skills/detk/{SKILL.md,references/airway.md,references/commands.md}`, identical to `skills/detk/` (`diff -r`).
  - It wrote `skills-lock.json` (ref node/38-agent-skills, skillPath skills/detk/SKILL.md).
  - Only the npm cache landed in the scratch home.
- **Mutation test** (on a copy of `tests/skills/test_skills.py`, run against mutated copies of the skill text). Script: `/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/rr42/mut.py`.
  - Caught (20):
    - a missing `<cov_fn>` in the deseq2 block, in SKILL.md and in airway.md;
    - a missing `<gmt_fn>` on a backslash-continued fgsea line;
    - `--last-term-onlyx`, `--report-directory` and `-k` (for `-c`) in prose;
    - a bogus option in blocks fenced `sh`, `shell`, and `console` with a `$` prompt;
    - typo'd subcommands in a block (`detk-norm deseq`, `detk-report generat`) and in prose (`detk-norm fpk`);
    - a typo'd tool in prose (`detk-reprt`);
    - `--filter-unannotated` placed after `detk-filter`;
    - the `detk norm deseq2 --bogus` form;
    - two edited usage lines in commands.md.
  - Missed (7):
    - a bogus option in a `~~~` fence, in an indented code block, and after `cd x &&`;
    - commands in plain or bold prose without backticks;
    - a usage block under a `###` heading.
  - Missed as expected, and as DETK-0010 now says: a wrong DE column name for `-c`, a misspelled filter function, and the re-added `--size-factors` (declared but ignored).
- **Airway run without R:**
  - Directory: `/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/rr42/air/`.
  - Inputs were `counts.csv` and `sample_info.csv`, copied from the earlier review's reproduction. detk was installed into a fresh venv by the skill's own instructions: `>=1.0` found nothing, then the GitHub fallback.
  - Ran and succeeded:
    - `detk-stats summary --log --color-col=dex`;
    - `detk-filter 'nonzero(all) >= 0.5'`, which kept 24,706 (the skill says about 24,700);
    - `detk-norm deseq2` without `--size-factors`. The size factors (1.024, 0.896, 1.179, 0.670, 1.178, 1.399, 0.921, …) are in the report JSON, as the skill now says;
    - `detk-outlier entropy`;
    - `detk-report generate`, which reported 9 modules and wrote `ro-crate-metadata.json` in the working directory, as the skill now says.
  - Failed for lack of R, as expected: `detk-wrapr check`, `detk-transform vst` and `detk-de deseq2`. `detk-norm library` still crashes, which confirms the skill is right to warn against it.
  - Filter forms from the skill, checked on airway:

    | Expression | Kept | Check |
    |---|---|---|
    | `nonzero(all) >= 1` | 33,469 | at least one sample, as the skill warns |
    | `nonzero(all) >= 8` | 18,870 | matches a pandas count of genes nonzero in all 8 |
    | `nonzero(dex[trt]) >= 0.5` | 25,267 | matches pandas |
    | `nonzero(dex) > 0.5` | 24,270 | |

## Findings

1. **`skills/detk/references/commands.md:74-77`: the copied usage still advertises `--size-factors=FILE`, and says it writes a file.** Severity: low.
   - SKILL.md:128-129 dropped the option, but the agent is told to consult this file "when in doubt". Nothing there says the option is ignored in this version.
   - The usage block has to stay verbatim for the test, so the fix is a note under it, not an edit inside it: "ignored in this version: no file is written; the size factors are in the report".
   - The CLI bug itself still needs an issue (earlier question 2).

2. **`tests/skills/test_skills.py:39,117-140`, against `docs/agent-skills.md:80-83` and DETK-0010 (Option A): a few code-block forms go unchecked.** Severity: low.
   - The docs page says "every `detk-*` command line in its code blocks" is parsed. In fact these are not read:
     - `~~~` fences, which CommonMark treats as fenced code;
     - indented code blocks;
     - a `detk-*` command that does not start its line (`cd x && detk-…`, `$(…)`);
     - a usage block under a heading other than ``## `detk-…` `` followed directly by a `text` fence. That one is skipped silently.
   - The skill uses none of these forms today, so nothing is unchecked now.
   - Fix: add `~~~` to `FENCE`, and fail if a `text` block in a skill file is not matched by the usage-block pattern. Alternatively, add "``` fences" to the wording. DETK-0010's revisit clause already covers commands outside code.

3. **`docs/agent-skills.md:33-35`: the page sends readers to `index.md#installation`, which still says plain `pip install de_toolkit`.** Severity: low.
   - That is the line that installs the broken 0.9.12 until 1.0 is on PyPI.
   - It resolves itself when the release is published. `docs/index.md` is outside this node's scope, so this is a note for the release step rather than a change here.

## Questions

1. The R half of the airway run is NOT verified by this review: `detk-transform vst`, `detk-de deseq2` (`counts ~ cell + dex[untrt]` and the `dex__trt__*` columns), the Ensembl-to-Entrez join under detk's interpreter, `detk-enrich fgsea` against WikiPathways with `-c dex__trt__log2FoldChange`, and the final report with DE and enrichment views. R is not installed here. That falls to Adam at s3: run the skill from a fresh project with R. The "test with R (bioconda)" CI job (pending at review time) covers the DESeq2 commands through `examples/airway/run.sh`, but not through the skill and not fgsea.
2. Still open from the earlier review: should the `--size-factors` no-op and the `detk-norm library` crash be filed as issues now? The developer says #40 (release/tpm-cpm) fixes `library`; once it merges, the skill should offer `library` again and restore its usage block.
3. Still open: `detk-util tidy -p` writes the sample table with an extra `counts` column of zeros (re-confirmed on airway: `sample,cell,dex,counts`). The skill tells the agent to pass the tidied table on, and the DESeq2 design names `counts` on its left side. Is the column intended, and does it interfere with the design? This needs R to check.
4. fgsea ranking: the skill keeps `__log2FoldChange` to match the published example, and now names `__stat` as the alternative and asks the agent to say which it used. Adam can confirm that choice, or record a decision to move both the skill and the example to `stat`.
