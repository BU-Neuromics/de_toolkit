---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/deps, step: s1}
applies: [release/deps]
allowed_by: [reasonable]
reason: DETK-0016 says 3.10 users stay on 0.9.x, but 0.9.12 fails on 3.10+
---

# Python 3.10 users have no working release; DETK-0016's 0.9.x line corrected

## Background

DETK-0016 (Accepted, option A) drops Python 3.10 in 1.0 so the lock can
carry the patched Pillow. Its Consequences say "Under A: 3.10 users stay
on 0.9.x". That is not so: 0.9.12, the newest 0.9.x and the last release
on PyPI, imports `Mapping` from `collections`, removed in Python 3.10, so
every command fails on 3.10 and newer with `ImportError: cannot import
name 'Mapping' from 'collections'` (reproduced in a clean venv in the
review of #42; `skills/detk/SKILL.md` says the same).

## Context

- An Accepted record's text is the human's; an agent does not rewrite
  it. Adam asked (2026-11-09) for this correction to be recorded
  Provisional.
- What 3.10 users actually have: no working release. 0.9.12 runs only on
  Python 3.9 or older; 1.0 needs 3.11 or newer; the code between them was
  never released.
- The 1.0 CHANGELOG already leaves the 0.9.x claim out.

## Options

### Option A: a correcting record

This record states the fact and names the line it corrects; DETK-0016
stays as accepted, and a reader of either finds the other.

### Option B: revise DETK-0016's text

`cogit decision revise` on the Accepted record. Changes text Adam
accepted, under an agent's name.

## Decision

Option A. DETK-0016's Consequences should read: Python 3.10 users have
no working release; 0.9.12 fails on Python 3.10 and newer and 1.0 needs
Python 3.11, so a 3.10 user upgrades Python. Nothing else in DETK-0016
changes.

## Consequences

The release notes for 1.0 say plainly that 1.0 needs Python 3.11 and
that 0.9.12 does not run on 3.10 or newer. Adam may fold this into
DETK-0016's text when he reviews it, and then supersede this record.
