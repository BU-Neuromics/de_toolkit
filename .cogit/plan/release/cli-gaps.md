---
kind: task
objective: 'The remaining CLI gaps Adam put in 1.0 are closed: --column-data, exit codes and shell completion (DETK-0025, DETK-0030, DETK-0031, DETK-0032)'
acceptance:
  - 'detk-filter --column-data is removed or kept per DETK-0030, and the cli-pin table and CHANGELOG say which'
  - 'every detk command exits with the codes DETK-0031 sets; failures print a one-line cause on stderr, with the traceback only under --verbose; cli-pin pins each code; help states the codes in its epilog'
  - 'shell completion is available as DETK-0032 chooses, a test checks it covers every command and subcommand, and no runtime dependency is added unless DETK-0032 chooses one'
  - 'the skill''s usage blocks and DETK-0010''s test still pass'
from: [DETK-0025, DETK-0030, DETK-0031, DETK-0032]
scope: [de_toolkit/common.py, de_toolkit/norm.py, de_toolkit/de.py, de_toolkit/enrich.py, de_toolkit/transform.py, de_toolkit/filter.py, de_toolkit/stats.py, de_toolkit/outlier.py, de_toolkit/wrapr.py, de_toolkit/report.py, de_toolkit/util.py, tests/cli/, tests/filter/, skills/detk/references/commands.md, pyproject.toml, uv.lock, +CHANGELOG]
prev: [DETK-0030, DETK-0031, DETK-0032, release/cli-migrate]
---

# Close the remaining CLI gaps

## Implementation plan

- [ ] @developer Carry out DETK-0030 (--column-data) and DETK-0031 (exit codes, stderr messages, help epilog) across the commands, with pins; open the PR <!-- s1 -->
- [ ] @reviewer Review the exit codes and messages from an agent's side: each failure class gives its code and a cause to act on <!-- s2 -->
- [ ] @developer Add shell completion per DETK-0032 with its coverage test; CHANGELOG <!-- s3 -->
- [ ] @reviewer Review the PR <!-- s4 -->
- [ ] @human Accept <!-- s5 -->

## Notes

Planned 2026-11-19 on Adam's answer to DETK-0025 ("address all the CLI
gaps"). Gaps 1 (umbrella command) and 3 (metavars) are in
release/cli-migrate; gap 2 (--size-factors) is release/size-factors. The
choices here wait on DETK-0030, DETK-0031 and DETK-0032. Edits the same
modules as release/size-factors (norm.py): whichever lands later merges.
