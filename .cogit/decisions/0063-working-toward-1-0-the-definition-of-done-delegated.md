---
template: note
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release}
applies: [release]
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's words relayed by the driver session, 2026-11-20: \"I'd like for us to develop a set of stopping criteria that describes what done means for a 1.0 release, then you work autonomously through cogit to complete it.\" \"Decisions: delegate.\" \"Plan PR: they may merge on green CI.\" \"Wait for my go ahead on final release.\" On DETK-0002: \"let's defer.\""}
---

# Working toward 1.0: the definition of done, delegated decisions, plan PRs on green, the release Adam's

- Proposed by: the planning session, 2026-11-20, to record how Adam
  asked the project to run from now on, relayed by the driver session

## Context

On 2026-11-20 Adam told the driver session: "I'd like for us to develop
a set of stopping criteria that describes what done means for a 1.0
release, then you work autonomously through cogit to complete it." He
granted, in his words: "Decisions: delegate."; "Plan PR: they may merge
on green CI."; "Wait for my go ahead on final release."; and on
DETK-0002 (rewriting the PCA_tester data out of git history): "let's
defer." This extends the standing authorization of 2026-11-09, under
which a node's accept step is ticked for Adam, merging its PR, once a
fresh reviewer has approved it and CI is green.

## Decision

1. **The definition of done.** 1.0 is done when every criterion of the
   `release` node's acceptance holds. The planning session drafts those
   criteria, each checkable by a command, a test, a CI job or a state
   in this record; Adam approves the draft before it is committed.
   Until then the release node's acceptance stands as written.
2. **Decisions are delegated.** A decision record may be accepted on
   the proposing session's recommendation when it stays within the 1.0
   definition of done and changes neither the 1.0 promise (DETK-0001,
   DETK-0025) nor the 1.0 scope. The driver session judges that and
   tells the session; the acceptance cites "Adam's delegation via the
   driver session, 2026-11-20" (`cogit decision accept ... --via`).
   Each record accepted this way is listed for Adam, who may reopen it.
   A decision that changes the promise or the scope stays Proposed for
   Adam.
3. **Plan PRs merge on green.** A pull request that changes only the
   record (`.cogit/`: plan, decisions, journal) may be merged by the
   session that opened it, with a merge commit, once every CI check on
   its head has passed.
4. **Node PRs** merge as on 2026-11-09: a fresh, independent reviewer
   approves (the node's review step), CI is green on the head with main
   merged in, including the R job, and the session ticks the node's
   `@human` accept step citing that authorization, which merges.
5. **The release is Adam's.** The version bump PR may be prepared, but
   the tag, the PyPI upload, the GitHub Release and the Zenodo DOI wait
   for his explicit go-ahead: release/cut's `@human` steps are his and
   are not ticked under this delegation.
6. **DETK-0002 is deferred.** It stays Proposed and Adam's. It no
   longer gates the work before the cut: release/cut no longer lists it
   in `prev:`, and instead has its own `@human` step, just before his
   go-ahead to tag, to answer it, since a rewrite (its Option B) must
   come before the tag. Nothing is done on it until he answers.
7. **Still Adam's:** anything only he can check (local R runs, account
   settings such as PyPI Trusted Publishing and Zenodo), anything
   outward-facing beyond the repository's own PRs and issues, and any
   change to the 1.0 promise or scope.
8. **cogit's merge policy stays `never`.** `merge:` in
   `.cogit/project.yaml` governs `cogit node merge`, an agent merging a
   node's PR without a person's accept; it has no notion of a plan PR.
   Items 3 and 4 work through the accept tick and an ordinary merge, as
   since 2026-11-09, so the policy is left alone.
