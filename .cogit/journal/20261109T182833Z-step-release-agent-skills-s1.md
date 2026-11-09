---
kind: step
time: 2026-11-09T18:28:33Z
by: DETK/developer
node: release/agent-skills
step: s1
branch: node/38-agent-skills
verdict: done
commits: [dc3f248, 14da646, 7b41bc8, 39efc3e]
decisions: [DETK-0009, DETK-0010]
---

# Done: Write the skills under `skills/` in the layout `npx skills` reads, check `npx skills add` installs them, document them; open the PR

## Summary

One detk skill under skills/ with airway and command references, a docs page, README and CHANGELOG, and a test that checks the skill's commands against --help (PR #42). npx skills add installed it from the local path and from the branch into a scratch project. pytest 156 passed, 49 skipped; ruff and mkdocs --strict clean. Not yet run on airway (no R here).

## Artifacts

## Findings

## Questions
