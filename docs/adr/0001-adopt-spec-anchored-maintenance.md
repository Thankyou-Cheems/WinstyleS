# ADR-0001: Adopt Spec-Anchored Maintenance

Status: Accepted
Date: 2026-07-05

## Context

WinstyleS is a brownfield Windows utility with CLI, plugin, import, reporting,
and Web GUI surfaces. The previous `WinstyleS_开发框架.md` mixed historical
audit findings, roadmap status, and durable rules. Several items in that file
were later completed, but the document still read as active planning.

## Decision

Use spec-anchored development:

- `docs/ARCHITECTURE.md` describes the current implementation.
- `docs/specs/` contains durable cross-module contracts.
- `docs/PITFALLS.md` records incidents and maps them to specs.
- `docs/adr/` records process and architecture decisions.
- bd tracks executable backlog items.
- `AGENTS.md` acts as a short router to the canonical documents.

## Consequences

Future changes that alter import safety, Web API envelopes, or quality gates
must update the relevant spec before they are considered complete. Old planning
documents are historical evidence, not the active source of truth.
