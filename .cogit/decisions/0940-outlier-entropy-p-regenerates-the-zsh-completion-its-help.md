---
template: adr
state: Proposed
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/outlier-entropy-p, step: s1}
applies: [release-1-0-1/outlier-entropy-p]
issue: 225
---

# outlier-entropy-p regenerates the zsh completion its help change makes stale

## Background

detk ships shell completion scripts in `de_toolkit/completions/`
(`detk.bash`, `detk.zsh`, `detk.tcsh`). They are generated from the argparse
parsers by `python -m de_toolkit.completions._generate`, and
`tests/completion/test_completion.py::test_shipped_script_is_current` fails
when a shipped script differs from what the parsers give. The zsh script
carries each option's help text, including argparse's `(default: X)`.

## Context

- release-1-0-1/outlier-entropy-p (#222, PR #224) gives `detk-outlier
  entropy -p` the default 0.05 (DETK-0860). The help line now ends `between
  0 and 1 (default: 0.05)`, as DETK-0860's Consequences require.
- That makes `detk.zsh` stale: two lines (the `detk-outlier entropy` and the
  `detk outlier entropy` option lists) differ, and the completion test fails
  on the branch. bash and tcsh carry no help text and do not change.
- The node's scope lists `de_toolkit/outlier.py`, `tests/outlier/`,
  `tests/cli/`, the docs page, the skill's commands reference and the
  CHANGELOG; it does not list `de_toolkit/completions/`. The worker
  instructions are not to widen scope without a decision.
- Criteria: CI green on the PR; the shipped completion matches the shipped
  help; the reviewer can see that nothing changed outside scope except what
  follows mechanically from the in-scope change.

## Options

### Option A: regenerate `detk.zsh` in this node's PR, and add it to the scope

Two generated lines change, produced by the project's own generator; no
hand edit. CI passes and the shipped zsh completion shows the same default
as `--help`. Cost: the node's scope grows by one generated file.

### Option B: leave `detk.zsh` alone and let another node regenerate it

The scope stays as planned, but the PR's CI fails on the completion test
and main would ship a completion that disagrees with `--help` until someone
regenerates it. Any later node that touches a parser would regenerate it
anyway and pick up this change unexplained.

## Decision

Recommended: **Option A**. The file is generated output of the in-scope
parser change, the diff is the two help lines, and Option B leaves CI red
for no gain. Regenerated in 55b8ed9 on PR #224 pending this decision; if
rejected, that commit is reverted.

## Consequences

- The node's scope gains `de_toolkit/completions/detk.zsh` (generated).
- Other in-flight nodes that change a parser's help text
  (outlier-shrink-int, crate-inputs, ...) will regenerate the same file; the
  merges are simple (regenerate after merging main).
- Revisit if the completion scripts move out of the package or stop carrying
  help text.
