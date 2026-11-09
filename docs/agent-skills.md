# Agent skills

detk ships an [agent skill](https://agentskills.io/) so that a coding agent
(Claude Code, Codex, Cursor, OpenCode and the others the
[`skills`](https://github.com/vercel-labs/skills) installer supports) can run
a detk analysis for you: install detk and its R packages, check the inputs,
and drive the command line from a counts matrix and a sample information table
through filtering, normalization, differential expression and gene set
enrichment to a [detk report](report.md).

## Install the skill

From the project directory where you will run the analysis (Node.js 22 or
newer):

```bash
npx skills add BU-Neuromics/de_toolkit
```

The installer asks which agents to install the skill for. To install without
prompts, name the skill and the agent:

```bash
npx skills add BU-Neuromics/de_toolkit --skill detk -a claude-code -y
```

The skill goes into the project (for Claude Code, `.claude/skills/detk/`);
add `-g` to install it for your user instead. `npx skills list` shows what is
installed, `npx skills update` brings it up to date with the repository, and
`npx skills remove detk` removes it.

The skill teaches the agent to use detk; it does not install detk itself until
the agent follows its instructions. Python 3.10 or newer is needed, and R with
DESeq2, fgsea and logistf for the R-backed steps (see
[Installation](index.md#installation)).

## Use it

Ask the agent in plain words, naming your files and the comparison you want:

> Use detk to find genes differentially expressed between treated and
> untreated samples in `counts.csv`, with `sample_info.csv` as the sample
> table. Control for `batch`, use `untreated` as the reference, run fgsea
> against `h.all.v2024.1.Hs.symbols.gmt`, and make the report.

Agents load a skill when the request matches its description; you can also
name it (in Claude Code, `/detk`). The agent then:

1. checks that detk and R are installed (`detk-wrapr check`), installing what
   is missing if you let it;
2. looks at the two files and, if needed, tidies them with `detk-util tidy`;
3. runs `detk-stats summary`, `detk-filter`, `detk-norm deseq2`,
   `detk-de deseq2` and `detk-enrich fgsea` with your design formula;
4. runs `detk-report generate`, and reports the result tables, the number of
   significant genes, the top gene sets, and the paths to
   `detk_report/detk_report.html` and `ro-crate-metadata.json`.

It asks rather than guesses when the request leaves out the condition of
interest, the reference level or the gene set collection.

To try it on known data, ask the agent to run the airway example from the
skill's reference: it reproduces the [worked example](example.md) and its
report.

## What is in the skill

The skill lives in the repository under
[`skills/detk/`](https://github.com/BU-Neuromics/de_toolkit/tree/main/skills/detk):

- `SKILL.md`: what detk is, installation, the input formats, the analysis
  steps with the options that matter, and what to report back.
- `references/airway.md`: the [airway worked example](example.md) end to end,
  including the data preparation and the Ensembl to Entrez join that
  enrichment against WikiPathways needs.
- `references/commands.md`: the usage of each command the skill uses, as the
  commands' `--help` prints it.

The skill describes the command line, detk's [stable interface](index.md#stability).
detk's test suite (`tests/skills/test_skills.py`) checks every `detk-*`
command line in the skill against the installed CLI's usage, so a change to a
subcommand or option that is not carried into the skill fails CI.
