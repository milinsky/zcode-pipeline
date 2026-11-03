# ZCode Pipeline

**A multi-agent development conveyor for ZCode: from a raw request to an accepted, verified change — with enforced briefs, architecture, decomposition, triple review, QA and a living knowledge base.**

English Core since v2.0: all agent prompts and coordinator rules are English; agents communicate with users and write project artifacts in the user's language.

[![English](https://img.shields.io/badge/README-English-blue)](README.en.md)
[![Русский](https://img.shields.io/badge/README-Русский-red)](README.ru.md)
[![中文](https://img.shields.io/badge/README-中文-green)](README_CN.md)
[![License: GPL v3](https://img.shields.io/badge/License-GPL--3.0--or--later-blue)](LICENSE)

## Why

LLM coding agents are fast — and unreliable in the same predictable ways: they guess requirements, skip steps, claim tests pass without running them, and forget everything between sessions. ZCode Pipeline turns development into a **conveyor of specialized subagents** where every stage is gated by the previous one's artifact, every claim must be proven by actual runs, and every accepted epic feeds a permanent project wiki.

## What you get

- **13 specialized agents** — initializer, briefer, architect, tech lead, technical writer, developer, security / goal / code reviewers, QA, manager, summarizer, analyst.
- **`/init-project` command** — detects the project stack, pulls current best practices from official sources into `.ai/guides/`, generates the project `AGENTS.md`.
- **`/analyze` command (analysis track)** — deep project or feature analysis without development: brief → parallel expert audits (architecture / security / code quality / feasibility) → verified, prioritized synthesis report with a bridge into the development conveyor.
- **`pipeline` skill** — rules for the coordinating main agent: stage order, escalation routing, review cycles, task statuses, commit policy.
- **Knowledge base (`.ai/docs/`)** — living per-component wiki + epic chronicles, updated after every accepted epic.

## Commands

- `/init-project` — stack detection, best-practice guides (`.ai/guides/`), project `AGENTS.md`; once per project.
- `/analyze "<project or feature>"` — expert analysis without development: brief → parallel expert audits → verified synthesis report → optional bridge into the conveyor.
- `"Run the pipeline: …"` — the full development conveyor (brief → architecture → tasks → code → triple review → QA → acceptance).
- `/self-test` — regression test of the conveyor itself: 13 agent-contract probes on a sandbox fixture.
- `/pipeline-status` — live conveyor status: active epic(s), stage, open cycles, spend vs budget.
- `/fast "<small change>"` — fast-track profile: brief → developer → code review (plus security on risk triggers) → commit; for small reversible edits.

## Install

1. ZCode → Plugin Marketplace → **Add → Add Plugin Marketplace** → paste this repository's URL.
2. **Personal → ZCode Pipeline → Install** → restart the session.
3. Verify: 13 agents, the `/init-project` command, the `pipeline` skill.

## Quick start

```
/init-project                              # once per project: stack, guides, AGENTS.md
"Run the pipeline: <your feature request>" # the coordinator skill takes over
/analyze "<project or feature>"            # expert analysis, no code changes
```

Full documentation: **[English](README.en.md) · [Русский](README.ru.md) · [中文](README_CN.md)** · History: [CHANGELOG.md](CHANGELOG.md)

## License

[GPL-3.0-or-later](LICENSE) · © 2026 Mikhail Ilinsky
