---
template: adr
state: Accepted
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/agent-skills, step: s1}
applies: [release/agent-skills]
allowed_by: [reasonable]
reason: "npx skills reads skills/<name>/SKILL.md; one skill with references loads on any detk request and keeps install and flow together"
revisions:
  - {date: 2026-11-09, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-09: accept with release/agent-skills"}
---

# One agent skill, detk, under skills/ with reference files

## Background

An agent skill is a directory holding a `SKILL.md` (YAML front matter with
`name` and `description`, then instructions) that coding agents load when a
request matches its description. #38 asks for detk skills installable with
`npx skills add BU-Neuromics/de_toolkit`, so that an agent can be pointed at
detk in an analysis workflow. The layout and the skill names are what users
type (`--skill detk`) and what later nodes extend, so they are hard to change
once 1.0 ships.

## Context

- The `skills` CLI (vercel-labs/skills, 1.7.6 checked) discovers
  `SKILL.md` files in a repository's root, `skills/`, `skills/.curated/`,
  and agent directories such as `.claude/skills/`, up to three levels deep;
  `name` must be lowercase with hyphens. It copies the whole skill directory,
  references included, into the project (`.claude/skills/<name>/` for
  Claude Code).
- An agent sees every installed skill's description and loads the body on a
  match; reference files are read only when the body points to them.
- The work an agent does with detk is one flow: install detk and R, check
  the inputs, filter, normalize, test, enrich, report. Installation is only
  needed as part of that flow.
- Criteria: the skill triggers on any detk or RNA-seq DE request; the body
  stays short; nothing in `.claude/skills/` of this repository is picked up
  by mistake (the repository's own agent configuration is separate).

## Options

### Option A: one skill, `skills/detk/`, with `references/`

`SKILL.md` covers what detk is, installation, inputs, the analysis steps and
what to report; `references/airway.md` the worked example and
`references/commands.md` the usage of each command used. One name to install
and to describe; the flow and its prerequisites stay together; long material
loads only when needed.

### Option B: several skills (`detk-install`, `detk-de-workflow`, one per tool)

Finer triggering, but the workflow skill would have to send the agent to the
install skill, which may not be installed, and per-tool skills duplicate the
docs and multiply the descriptions competing for the agent's attention.

### Option C: a root `SKILL.md`

Discovery reads a root `SKILL.md` first and it shadows anything nested, so
the repository could never ship a second skill.

## Decision

Option A. The analysis is one flow, and a single `detk` skill with reference
files keeps it whole while the `skills/` container leaves room for more
skills later. New commands (TPM/CPM in `detk-norm`, #24; `detk-util`
annotate, #29; the commands of #25) go into this skill, in `SKILL.md` where
they change the flow and in `references/commands.md` otherwise.

## Consequences

- `npx skills add BU-Neuromics/de_toolkit --skill detk` is the stable
  install line; renaming the skill would break it.
- A second skill (for example a report-reading or QC skill) goes in
  `skills/<name>/` beside it.
- Revisit if `SKILL.md` grows past what an agent should load at once, by
  moving more of it into `references/`.
