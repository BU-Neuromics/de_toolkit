---
kind: task
objective: uv.lock carries the patched Pillow and certifi, so the Dependabot alerts on main close
acceptance:
  - the Dependabot alerts for Pillow and certifi on main are closed by the update
  - the full test suite, with R, passes on the updated lock
scope: [uv.lock, pyproject.toml, README.md, docs/index.md, docs/agent-skills.md, .github/workflows/ci.yml, +CHANGELOG]
issue: 53
visited: b94644c
prev: [DETK-0016]
---

# Update locked dependencies

## Implementation plan

- [x] @developer Update uv.lock (`uv lock --upgrade-package pillow --upgrade-package certifi`, and any other package an open alert names), run the suite; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42 (the push notices of 45 Dependabot alerts).
