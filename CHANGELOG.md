# CHANGELOG — ZCode Pipeline

Format: bundle/plugin versions. Source of truth — this repository (`zcode-pipeline/{agents,commands,skills,assets}`). All entries in English.

## v1.2.0 — 2026-11-03

Analysis track: deep project/feature analysis without development, parallel to the conveyor.

### Added

- **`analyst` agent** (expert synthesizer): input — an analysis-track brief plus expert audit
  reports; selectively verifies claims against the actual code (manager pattern), resolves
  inter-expert contradictions by evidence, prioritizes findings (severity × effort) and writes
  `.ai/analysis/{epic}-{date}/REPORT.md` + one line in `.ai/docs/INDEX.md` (new "Analyses"
  section). Ends with a bridge: which findings are ready to become a development epic.
- **`/analyze` command**: brief (track: analysis) → parallel expert fan-out by focus →
  coordinator saves reports → analyst → summary + bridge to the user.
- **Analysis modes** in `architect` (architecture audit), `security-review` (whole-project
  security audit), `code-review` (code-quality/tech-debt audit), `tech-lead` (feature
  feasibility): activated by an analysis-track brief input; the conveyor modes are unchanged
  and distinguished by the input artifact type.
- `briefer`: new `analysis` request category; analysis briefs carry `**Трек:** analysis` and
  success criteria formulated as questions the report must answer; focus recorded
  (security | architecture | quality | all | feasibility).
- `pipeline` skill: "Analysis track" section (fan-out rules, no QA/Manager/review cycles in
  this track, bridge procedure).

### Compatibility

The development conveyor is untouched: all gates, review cycles and statuses behave exactly
as before; the analysis track is opt-in via `/analyze` or an explicit analysis request.

## Licensing — 2026-11-03

- Added the canonical GNU GPL v3 text as `LICENSE` (SPDX: GPL-3.0-or-later).
- All README versions (EN/RU/ZH + brief) now carry the license notice, warranty
  disclaimer and a link to `LICENSE`.

## Documentation — 2026-11-03

- Multilingual README: brief `README.md` (English) + full versions — [English](README.en.md), [Русский](README.ru.md), [中文](README.zh.md).
- Removed all local/machine-specific paths from installation instructions: the only install channel is this GitHub repository (marketplace) plus the bundle fallback.
- CHANGELOG switched to English; future commits in English.

## v1.1.1 — 2026-11-03

Fixed marketplace installation ("Marketplace manifest not found in directory").

### Changed

- Canonical structure: the marketplace is the repository root with `marketplace.json`
  (name `milinsky-agents-bundle`, plugin `zcode-pipeline`, source `./zcode-pipeline`);
  the plugin moved into the `zcode-pipeline/` directory (directory name must equal the manifest name).
- `build_bundle.py` reads from `zcode-pipeline/`; bundle version comes from the plugin manifest.

## v1.1.0 — 2026-11-03

Packaged the system as a ZCode plugin; the repository became a self-contained source of truth.

### Added

- **Plugin**: `.zcode-plugin/plugin.json` manifest (components: agents, commands, skills).
  Installable from a marketplace (GitHub repo or local directory).
- **`pipeline` skill** (`skills/pipeline/SKILL.md`): conveyor rules for the coordinating
  main agent — stage order, escalations to the Tech Lead consultant, review cycles
  (all findings incl. MINOR/NIT are mandatory), interactive question rendering, task
  statuses, commit-only-after-ACCEPTED. Triggers live in the frontmatter. Previously
  these rules existed only in the bundle header.
- **`assets/AGENTS-template.md`**: global-rules template with `{ОБРАЩЕНИЕ}`/`{ЯЗЫК_ОБЩЕНИЯ}`
  personalization placeholders — the builder no longer depends on the live installation.

### Changed

- `scripts/build_bundle.py`: builds the bundle from the repository files; the bundle now
  includes the skill section and the `~/.zcode/skills/pipeline/SKILL.md` install path.
- README: plugin as the primary install channel, bundle as fallback.

## v1.0 — 2026-11-02

First successful bundle: 12 agents + `/init-project` + optional personalized global AGENTS.md.

### System history (pre-v1.0)

- **Base 10 agents.** Conveyor: Briefer → Architect → Tech Lead → Tech Writer → Developer →
  Reviews (Security/Goal/Code) → QA → Manager. System prompts in Russian, tuned for GLM
  models: structured verdicts, Phase 0 gates, `!!! ESCALATION !!!` protocol (one per task),
  "gross violations" sections. Inspired by the author's OpenCode agent set — best ideas
  adopted (escalations, task template, review cycles), not copied.
- **Interactive questions.** Subagents have no interactive tool, so agents return
  structured "## Вопросы пользователю" blocks (options + "(Recommended)"); the coordinator
  renders them interactively with free-form input always available.
- **`summarizer` agent + knowledge base.** After ACCEPTED: `.ai/docs/` — per-component wiki
  pages (rewritten to current code state, "verified at commit" stamp), epic chronicles,
  INDEX.md, manual-checklist.md. Reading is wired into five reader agents' prompts; the
  global AGENTS.md points to it ("Karpathy-style wiki").
- **`initializer` agent + `/init-project`.** Stage 0: empty project → interactive stack
  selection (popular stacks, multi-select, free input with normalization); existing project →
  stack from manifests/linter configs + confirmation. Produces `.ai/guides/{tech}.md`
  (best practices from official/curated sources, ≤200 lines, dated, sourced) and the project
  `AGENTS.md` (base rules with `source=file|embedded` — a live global file always wins;
  otherwise an embedded template). Universal rules in every guide: no code comments (except
  annotations/docstrings); no co-authors in commits; full typing for optionally-typed
  languages; no references to `.ai/` in code/README. Embedded-template personalization
  (name/role, language) is asked interactively; re-init never re-asks.
- **Battle-tested on real epics** (a greenfield CLI project):
  - Epic 1 (6 tasks, 98 tests): full cycle; a Security escalation (`--dict /dev/zero`)
    resolved by the Tech Lead (S_ISREG guard; a MemoryError had been masquerading as
    exit code 1 "WEAK").
  - Epic 2 — a local web GUI (3 tasks, +59 tests): a Tech Writer escalation (import
    allow-list contradiction), a Security MEDIUM finding worse than reported
    (negative Content-Length), and a Code-review BLOCKER (JS sending DOM ids instead of
    class names — the browser button always got 400 while all automated tests were green).
    All closed through review cycles; Manager ACCEPTED; knowledge base updated.

### Known notes

- Subagents cannot ask questions directly — interactivity goes through the coordinator only.
- Newly created agent types register between turns / at session start.
- A user's global gitignore may hide `.ai` and `AGENTS.md` — conveyor commits need `git add -f`.
- Plugin-provided agents register with a `zcode-pipeline:` prefix; the skill instructs the
  coordinator to use the actual session registry names.
- Embedded-mode initializer personalization on a clean machine — pending author's test.
