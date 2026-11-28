---
kind: task
objective: detk-outlier entropy without -p runs with the percentile DETK-0860 settles, instead of failing on a None it cannot read as a float
acceptance:
  - 'reproduced first: on v1.0.0, ''detk-outlier entropy counts.csv'' (no -p) exits 2 with ''argument -p/--percentile: invalid float value: None''; a test shows it, and after it does what DETK-0860 decides, stated in --help, docs/tools/outlier.md and the skill''s commands reference'
  - '-p given behaves as before (DETK-0200: a fraction in (0, 1), anything else a usage error); no option added; CHANGELOG 1.0.1 under Fixed'
from: [DETK-0200, DETK-0860, DETK-0940]
prev: [DETK-0860, release-1-0-1/count-checks-readers]
scope: [de_toolkit/outlier.py, de_toolkit/completions/detk.zsh, tests/outlier/, tests/cli/, +docs/tools/outlier.md, +skills/detk/references/commands.md, +CHANGELOG]
issue: 222
visited: 5d8ae02
---

# detk-outlier entropy runs without -p

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Found by the count-checks-readers session (its reader test passes `-p 0.05`
to get past it); reproduced by the plan session, 2026-11-27, on a v1.0.0
install: no `-p` exits 2 with `invalid float value: None`, `-p 0.5` on the
same file runs. No help text, doc, docopt-era usage or DETK record states a
default, so what the no-`-p` case does is DETK-0860: accepted 2026-11-27, `-p`
defaults to 0.05, the value every documented run uses.
It also waits on count-checks-readers (PR #203), which edits the same lines of
`main()` in de_toolkit/outlier.py; once both land, that test's `-p 0.05` can
stay (it tests the reader, not the default).

DETK-0940 (accepted 2026-11-27) adds `de_toolkit/completions/detk.zsh` to the
scope: the zsh completion carries the help text, so `-p`'s stated default is
regenerated into it (`python -m de_toolkit.completions._generate`).
