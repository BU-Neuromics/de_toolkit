---
kind: task
objective: 'The detk agent skill covers the commands merged for 1.0: detk-util gather and annotate, detk-norm cpm and tpm, and detk-norm library again'
acceptance:
  - the skill and its command reference name each new command with its real usage, and the drift test passes against them
  - the skill starts from quantifier outputs with detk-util gather where the airway example allows
  - 'the skill no longer warns against detk-norm library (skills/detk/SKILL.md, the paragraph after the deseq2 example) and recommends it alongside deseq2, fpkm, cpm and tpm'
scope: [skills/, docs/agent-skills.md, tests/skills/, +CHANGELOG]
prev: [release/gather, release/padded-ids]
issue: 62
visited: a328c16
---

# Bring the agent skill up to date

## Implementation plan

- [x] @developer Add the new commands to the skill and its references, restore `detk-norm library`; open the PR <!-- s1 -->
- [x] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Acceptance revised 2026-11-09 from the review of de_toolkit#57.

Planned 2026-11-09 on Adam's word. From the reviews of de_toolkit#42 and #52: the skill predates the commands merged for 1.0.
