---
kind: step
time: 2026-11-20T13:48:43Z
by: DETK/reviewer
node: release/tutorial-harness
step: s2
branch: review/tutorial-harness
verdict: changes
commits: []
decisions: []
---

# Changes asked: review of the tutorial runner, its CI wiring and docs (PR #84)

## Summary

The runner meets the node's acceptance and DETK-0064 Option A, and it is sound
enough for the three tutorial nodes to build on. Two small changes are asked
before approval: the check that markers stay hidden on the site never runs in CI,
and the how-to says something wrong about `fails` blocks. Everything else is
either fine or a nit.

What I checked: I read the full diff (the runner, conftest, fixture pages, tests,
ci.yml, mkdocs.yml, the two docs pages and the CHANGELOG). `uv run pytest
tests/tutorials` gives 31 passed and 2 skipped; with `--group docs` it gives 32
passed and 1 skipped (the empty page set). `mkdocs build --strict` is clean. All
CI checks on 56779be pass, including `test with R (bioconda)`, where the log
shows `mlr 6.22.0` and 1817 passed, 15 skipped. I also probed the runner and the
real mkdocs-material build with scratch pages, which are not committed.

Developer's choices made within the node, checked against DETK-0064:
- `...` wildcard plus `expect regex`: this is the "exactly, or by a pattern"
  the ADR asks for. A literal `...` in real output still matches, so the only
  cost is a looser check. Fine.
- expect compares stdout, and stderr after a `fails` block, with `expect
  stdout|stderr` to override: this matches the ADR ("the output shown is its
  stderr"). Fine.
- hidden blocks go inside an HTML comment. I checked this with a real `mkdocs
  build --strict` that included passes.md plus a hidden block indented inside
  an admonition and holding `--flag -- y`. Nothing showed outside comments: the
  only visible "tutorial" text was the edit-page URL, and the code was not
  visible. The runner parsed the indented hidden block as hidden. Fine.
- `TUTORIAL_SRC` for data committed beside a page: this is needed for the
  quantifiers tutorial. Fine.
- The R job fails rather than skips when a requirement is missing
  (`DETK_TUTORIALS_REQUIRE_ALL=1`): this is what "all of them in the R job"
  needs. Fine.
- The "collector" is a parametrized test over `discover()`, not a
  `pytest_collect_file` hook. One test per page, `-k` works, so it meets the
  intent.

Skips in the R job: `tests/tutorials` shows 2 skips there. One is
`test_tutorials.py` with an empty parameter set, which is expected because there
are no pages yet. The other is
`test_markers_and_hidden_blocks_do_not_show_on_the_site`, because `markdown`
and `yaml` are not installed in that job. The second skip is expected given how
the test is written, but see finding 1.

## Artifacts

## Findings

1. **Changes asked: the check that markers don't show on the site runs in no
   CI job.** `test_markers_and_hidden_blocks_do_not_show_on_the_site` calls
   `importorskip("markdown")`. The uv test jobs sync `--dev` only, and the R job
   installs the `dev` group only, so this test is skipped in every CI job. The
   strict docs build does not check this either. The acceptance item "the
   markers do not show on the site" therefore has no check in CI, and the hidden
   blocks the tutorial nodes will use could start rendering after an extension
   or Markdown upgrade without anything failing. Asked: run this test where the
   docs group is installed. For example, add a step to the docs job:
   `uv run --group docs --group dev pytest tests/tutorials/test_tutorial_runner.py -k site`.
   Or make `markdown`/`pyyaml` available to a test job. I verified by hand that
   it holds today.

2. **Changes asked: docs/dev/tutorials.md is wrong about `fails` blocks.** It
   says "Files and variables the failing block made do not carry to the next
   block." Both carry. Files stay in the shared working directory, and the
   EXIT trap saves the shell state even when the block exits non-zero. A probe
   page with `X=...; touch made.txt; false` under `fails`, followed by
   `echo "$X"; ls made.txt`, passed. Asked: correct the sentence. Saying that
   both carry is the simpler fix, and the behaviour is reasonable.

3. Nit (document, or guard): a block that sets its own `trap ... EXIT` replaces
   the runner's state-saving trap, so nothing it set carries on. A probe with
   `trap 'echo mine' EXIT; Y=after_trap`, followed by `echo
   "${Y:-unset}"`, printed `unset`, and under nounset a plain `$Y` would fail
   with a confusing message. Either add a line to the how-to ("don't set an
   EXIT trap in a block") or save the state some other way.

4. Nit (document): an `expect` compares the output of the last bash block that
   ran, and that includes a hidden one. A hidden check between a visible command
   and its expect would compare the hidden block's output. One sentence under
   `hidden` would cover it.

5. Note, no change needed: `discover()` parses every page under `docs/` at
   collection time, so a malformed `<!-- tutorial` line on any docs page is a
   collection error for `test_tutorials.py`. It is loud, which is the right
   failure mode. A `TutorialError` raised during a run (a bad `expect` option)
   is not cached by `_Runs`, so it is re-raised on each call. That is harmless.

## Decisions

None needed. Every choice above is within the node and consistent with
DETK-0064.

## Questions
