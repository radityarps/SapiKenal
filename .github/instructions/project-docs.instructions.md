---
description: "Use when implementing features, modifying architecture, changing APIs, or answering project-specific questions. Enforces docs/ as the primary source of project truth and requires documentation updates alongside code changes."
applyTo: "**"
---

# Project Documentation Rules

## Source of Truth

Before implementing any feature, making architectural decisions, or answering project-specific questions, read the relevant file in `docs/`:

- [`docs/PRD.md`](../../docs/PRD.md) — requirements, output classes, dataset, online/offline strategy
- [`docs/Backend/Migration Plan/`](../../docs/Backend/Migration%20Plan/) — backend architecture, Phase 3 Go migration, Docker, benchmarks

Do not assume project context. If a relevant doc exists, read it first.

## Update Docs with Every Change

When making any code change, update the corresponding documentation in the same response:

| Change type | Update target |
|---|---|
| New feature or behavior change | `docs/PRD.md` (if scope changes) or relevant doc section |
| Backend architecture change | `docs/Backend/Migration Plan/` relevant file |
| API route, schema, or response shape change | `docs/Backend/Migration Plan/` or `docs/PRD.md` |
| New module, service, or component | Add description and integration notes to the relevant doc |

Never defer documentation updates — they must be part of the same edit as the code change.
