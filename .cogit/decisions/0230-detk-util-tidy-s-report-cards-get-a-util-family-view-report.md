---
template: adr
state: Proposed
authority: [human]
date: 2026-11-20
from: {node: release/tidy-output, step: s1}
applies: [release/tidy-output]
issue: 118
---

# detk-util tidy's report cards get a util-family view (report_specs.py, outside release/tidy-output's scope)

- Proposed by: the release/tidy-output developer session, 2026-11-20 (step s1)

## Background

The detk report (`detk_report.html`) shows one card per recorded step. Its
family (the section it sits in), title, description and view come from
`REGISTRY` in `de_toolkit/report_specs.py`; a module name missing there
lands in an "other" section, titled with its bare name (`tidy`), with no
description and only its raw JSON.

release/tidy-output makes `detk-util tidy`, `tidy-counts` and `tidy-covs`
record a module (`tidy`, `tidycounts`, `tidycovs`) in the report and the
Process Run Crate, as their help promises. `report_specs.py` is not in the
node's scope (util.py, crate.py, tests/util/, the quantifiers tutorial,
CHANGELOG).

## Context

- The developer profile says a new module registers its report view; every
  other detk-util module (annotate, gather, record) is in `REGISTRY` under
  the util family.
- Without an entry the node still meets its acceptance (module JSON and
  crate), but the report the quantifiers tutorial renders shows a bare
  "tidy" card under "other".
- The change is additive: three `REGISTRY` entries and a small key-value
  view (`build_tidy`: samples kept, each file's sample count, features, the
  samples each file lost), like gather's. No other module's view changes.

## Options

### Option A: the PR branch carries the entries (recommended)

Three `REGISTRY` entries and `build_tidy` in report_specs.py, with tests in
tests/util/test_tidy.py; the tidy cards sit in the util section with the
other detk-util steps.

### Option B: leave report_specs.py alone; a follow-up node adds the view

The node stays inside its scope; until the follow-up lands, the tidy
cards show under "other" with their raw JSON.

## Decision

Recommended: Option A. It is the small, additive piece that makes the
newly recorded steps read like the other detk-util steps in the report,
and it is what the help's report promise implies. The node's PR branch
carries it in its own commit, so Option B is a revert of that commit.

## Consequences

- report_specs.py joins this node's changes; reviewers check the view.
- If rejected, revert the report_specs.py commit (and its two tests); the
  rest of the node is unaffected.
