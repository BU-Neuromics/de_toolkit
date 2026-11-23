---
kind: step
time: 2026-11-23T17:57:15Z
by: DETK/developer
node: release/record-program
step: s1
branch: node/156-record-program
verdict: done
commits: [e9a8087]
decisions: []
---

# Done: As DETK-0390 is answered: write record's absolute program as its name when PATH finds the same file, otherwise relative as today; tests, schema description, CHANGELOG; open the PR

## Summary

record writes an absolute program by name when shutil.which finds the same file (directories resolved, file name kept, as _file_relpath compares), else relative to workdir; applied to params.argv/command and to detk-util's own argv (the program word located as the tail the command ends argv with), so the embedded payload and crate follow. Judgment calls within the node: 'same file' compares resolved directories + the file's name rather than os.path.samefile, so a symlink to the program elsewhere on PATH (e.g. a venv python linking to /usr/bin/python3) is not taken as the same program; the top-level argv was changed too, since leaving the ../ chain there would defeat DETK-0390's criterion (1). Two existing record tests now expect the interpreter by name (run() puts its directory first on PATH). Full suite 2559 passed, ruff clean, mkdocs --strict builds.

## Artifacts

## Findings

## Questions
