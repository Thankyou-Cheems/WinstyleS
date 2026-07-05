# Spec Refresh Proposal

Date: 2026-07-05

## Problem

The repository had two kinds of drift:

- `WinstyleS_开发框架.md` still described many already-completed Phase A-E tasks
  as planned work.
- Durable rules were duplicated across AGENTS, README, design notes, changelog,
  bd issue notes, and implementation tests.

## Proposal

Adopt a spec-anchored structure for future work:

- Keep architecture background in `docs/ARCHITECTURE.md`.
- Put durable contracts in `docs/specs/`.
- Use bd for the remaining executable backlog.
- Keep `AGENTS.md` short and route contributors to the canonical specs.

## Out Of Scope

- A full rewrite of every user-facing guide.
- Retroactive specs for every scanner implementation detail.
- High-risk apply behavior changes.
