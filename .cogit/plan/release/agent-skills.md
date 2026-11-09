---
kind: task
objective: Agent skills for detk in this repository, installable with npx skills add BU-Neuromics/de_toolkit, so an agent in an analysis workflow can drive the detk CLI
acceptance:
  - npx skills add BU-Neuromics/de_toolkit installs the skills into a fresh project
  - a skill takes an agent from a counts matrix and sample info through filter, norm, de and enrich to a detk report, on the airway example
  - a docs page (new, under docs/) and the README say how to install and use them
scope: [+README.md, +mkdocs.yml, +CHANGELOG]
---

# Agent skills

## Implementation plan

- [ ] @developer Write the skills under `skills/` in the layout `npx skills` reads, check `npx skills add` installs them, document them; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR, and run a skill on the airway example from a fresh project <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Added by Adam (2026-11-09). Skills describe the CLI, which DETK-0001 makes the 1.0
promise, so they land before the cut; they wait on no other node, though the
new commands of #24, #29 and #25 belong in them once merged.
