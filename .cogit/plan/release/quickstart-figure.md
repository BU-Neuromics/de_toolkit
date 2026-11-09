---
kind: task
objective: The quickstart's pipeline figure shows detk-util gather where it showed csvgather
acceptance:
  - docs/simple_pipeline.svg and .png show detk-util gather as the first step, with no csvgather box or link
scope: [docs/simple_pipeline.svg, docs/simple_pipeline.png, docs/quickstart.md]
prev: [release/gather]
issue: 59
visited: c060d5a
---

# Redraw the quickstart figure

## Implementation plan

- [x] @developer Redraw the SVG with detk-util gather, regenerate the PNG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word. From the re-review of de_toolkit#52: the quickstart text uses gather but its figure still shows csvgather.
