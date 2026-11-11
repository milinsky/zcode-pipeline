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

- **15 specialized agents** — initializer, briefer, architect, tech lead, technical writer, developer, security / goal / code reviewers, QA, manager, summarizer, analyst, plus two interactive design agents (spec-designer, ui-designer) for design dialogues without launching the conveyor; at project initialization the initializer offers to keep its working files out of the repository (global or local git ignore, user's choice).
- **`/init-project` command** — detects the project stack, pulls current best practices from official sources into `.ai/guides/`, generates the project `AGENTS.md`; interactively offers to keep the conveyor working files out of the repository (global or local git ignore, user's choice).
- **`/analyze` command (analysis track)** — deep project or feature analysis without development: brief → parallel expert audits (architecture / security / code quality / feasibility) → verified, prioritized synthesis report with a bridge into the development conveyor.
- **`pipeline` skill** — rules for the coordinating main agent: stage order, escalation routing, review cycles, task statuses, commit policy.
- **Knowledge base (`.ai/docs/`)** — living per-component wiki + epic chronicles, updated after every accepted epic.
- **12 `/git-*` commands** — safe git workflow replacing GUI clients: plan first, explicit confirmation for remote and destructive actions, `--force-with-lease` only, published history never rewritten without an explicit override.

## Commands

- `/init-project` — stack detection, best-practice guides (`.ai/guides/`), project `AGENTS.md`; interactively offers to keep the conveyor working files out of the repository (global or local git ignore, user's choice); once per project.
- `/analyze "<project or feature>"` — expert analysis without development: brief → parallel expert audits → verified synthesis report → optional bridge into the conveyor.
- `/spec-design "<topic>"` — interactive specification design without launching the conveyor: a guided design dialogue; accepted decisions are recorded immediately and versioned under `.ai/designs/{slug}/` (living design document + append-only decision log).
- `/ui-design "<topic>"` — a structured UI concept document (UX flow, components, style tokens, rationale) for UI-bearing work; launched strictly on your explicit request and persisted into the same designs home.
- `"Run the pipeline: …"` — the full development conveyor (brief → architecture → tasks → code → triple review → QA → acceptance).
- `/self-test` — regression test of the conveyor itself: 15 agent-contract probes on a sandbox fixture.
- `/pipeline-status` — live conveyor status: active epic(s), stage, open cycles, spend vs budget.
- `/fast "<small change>"` — fast-track profile: brief → developer → code review (plus security on risk triggers) → commit; for small reversible edits.
- Safe git workflow — 12 `/git-*` commands: `/git-status` (read-only inspection), `/git-commit` (proposes a message, commits after your confirmation), `/git-pull` / `/git-fetch` (sync), `/git-push` / `/git-push-force` (publish, `--force-with-lease` only), `/git-rebase` / `/git-squash` / `/git-undo` (history), `/git-stash` / `/git-branch` (workspace), `/git-resolve` (conflict resolution) — plan first, explicit confirmation for remote and destructive actions.

## Install

1. ZCode → Plugin Marketplace → **Add → Add Plugin Marketplace** → paste this repository's URL.
2. **Personal → ZCode Pipeline → Install** → restart the session.
3. Verify: 15 agents, the `/init-project` command, the `pipeline` skill.

## Quick start

```
/init-project                              # once per project: stack, guides, AGENTS.md, git-ignore offer
"Run the pipeline: <your feature request>" # the coordinator skill takes over
/analyze "<project or feature>"            # expert analysis, no code changes
/git-commit "fix: ..."                     # safe commit of staged changes
```

Full documentation: **[English](README.en.md) · [Русский](README.ru.md) · [中文](README_CN.md)** · History: [CHANGELOG.md](CHANGELOG.md)

## License

[GPL-3.0-or-later](LICENSE) · © 2026 Mikhail Ilinsky
