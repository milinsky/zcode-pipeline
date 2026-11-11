# CHANGELOG — ZCode Pipeline

Format: bundle/plugin versions. Source of truth — this repository (`zcode-pipeline/{agents,commands,skills,assets}`). All entries in English.

## v2.8.0 — 2026-11-11

Feedback hardening from the first production use: contract-mandated
time-to-market tables, raised budget defaults, a user-gated merge, and an
optional task validation pass.

### Added

- **Time-to-market tables**: two contract-mandated coordinator outputs — an
  estimate table immediately after the Technical Writer (per task,
  partition, and epic totals copied 1:1 from the task index) and an actuals
  table at COMPLETE (predicted vs actual agent time, active wall, pauses,
  tokens from the ledger and the summarizer report; honest gaps when the
  data is partial).
- **Task validation gate**: an interactive offer between the Technical
  Writer and the Developer to run a read-only Tech Lead validation pass
  over the created tasks (errors, typos, inconsistencies against the
  decomposition); content fixes return to the Technical Writer, micro-fixes
  may be applied by the coordinator.

### Changed

- **Budget defaults** raised 10x: 50,000,000 tokens for a full epic and
  10,000,000 for the fast-track; the semantics are unchanged (warn at 70%,
  stop-and-ask at 100%, changed only on an explicit user instruction).
- **Merging into main is user-gated**: no conveyor agent ever merges
  autonomously; after COMPLETE the coordinator offers the merge with three
  options (merge now with the exact command shown / keep the branch / the
  user merges themselves).

## v2.7.0 — 2026-11-05

Time-to-market metrics for epics: a coordinator timeline ledger, derived
pipeline estimates, and time/token facts in the epic summary.

### Added

- **Timeline ledger**: the coordinator maintains a per-epic append-only event
  log (stage open/close, pauses, epic start/finish) in the epic state file —
  agent time per stage and task and active wall time become measurable;
  question rounds, escalations, and silent session gaps are excluded by
  convention.
- **Derived pipeline estimates**: task headers, index partitions, and
  decompositions gain a pipeline-time estimate next to the person-hours
  estimate, derived as real_hours = human_hours / 8 (an empirical constant,
  subject to recalibration from the collected ledger data).
- **Epic time summary**: the final summary report gains a "Spend and time"
  section with token facts, agent and wall time per task and epic, and an
  actual-vs-predicted calibration ratio; the project metrics table gains two
  columns (agent/wall time, calibration). Epics without a ledger degrade
  gracefully: an honest gap is reported instead of blocking.
- `validate_prompts.py`: five new mandatory markers covering the formula and
  template contracts.

## v2.6.0 — 2026-11-04

Post-release hygiene: review verdicts are persisted as files; lease erratum.

### Added

- **Review verdict files**: the three reviewer agents (Security, Goal, Code)
  write their full verdict reports (verdict, findings, evidence) to the
  conveyor's reviews directory as part of their stage output — one file per
  reviewer per run, overwritten on re-review; the analysis track is
  unchanged. `validate_prompts.py`: three new mandatory markers covering the
  verdict-file contract.

### Fixed

- Refined lease form in `/git-push-force` is now quoted
  (`--force-with-lease='{ref}'`) per the universal operand-quoting rule;
  the operational Execute line is unchanged.
- README_CN.md: three corrupted Chinese fragments repaired (reconstructed
  from the English README counterparts).
- CHANGELOG: missing entries for v2.2.0–v2.3.2 backfilled from the GitHub
  release notes, each marked with a backfill note.

## v2.5.0 — 2026-11-04

Safe git workflow slash commands (GUI-client replacement).

### Added

- **12 safe git workflow commands** (`/git-status`, `/git-commit`, `/git-pull`,
  `/git-push`, `/git-fetch`, `/git-rebase`, `/git-squash`, `/git-push-force`,
  `/git-resolve`, `/git-undo`, `/git-stash`, `/git-branch`): plan first, explicit
  confirmation for remote and destructive actions, `--force-with-lease` only,
  published history is never rewritten without an explicit override, and the
  git-ignore decision saved at initialization is respected.
- `validate_prompts.py`: command checks — 17 command paths, per-command safety
  markers, personal-data scan of command bodies.

## v2.4.0 — 2026-11-04

Interactive git hygiene at project initialization.

### Added

- **Initializer git hygiene step**: at project initialization the agent
  interactively offers to keep its working files out of the repository via
  global or local git ignore (user's choice; the decision is persisted in the
  project AGENTS.md init stamp). Already-ignored and tracked artifacts are
  detected before asking; untracking requires explicit consent.
- Coordinator skill and `/init-project`: conveyor artifacts are force-added
  (`git add -f`) only when they are not ignored — the decision saved at
  initialization is respected.
- `validate_prompts.py`: four new mandatory markers covering the initializer
  git-hygiene contract.
- READMEs (EN/RU/ZH): the interactive git-ignore step documented.

## v2.3.2 — 2026-11-03

*Note: backfilled on 2026-11-04 from the GitHub release notes — the original CHANGELOG entry was missing.*

No emoji rule.

### Fixed

- Universal rule #5 — no emoji, decorative Unicode, or visual embellishments anywhere.
- Real-world finding: agents added emoji to project documentation — many professional projects reject PRs containing emoji.
- Scope: code, comments, docstrings, commit messages, README, guides, wiki, reports, task descriptions.
- Exception: only when the user explicitly requests emoji for a specific deliverable.

## v2.3.1 — 2026-11-03

*Note: backfilled on 2026-11-04 from the GitHub release notes — the original CHANGELOG entry was missing.*

Comment recommendation flow.

### Added

- A structured way to handle genuinely complex code that warrants explanation:
  1. Developer sees complex code → writes a "Comment recommendation" in the report (location, proposed content, why simplification won't work) — does NOT add the comment.
  2. Code-review evaluates: (a) simplify the code instead, (b) approve as docstring with contract info (WHY not WHAT), or (c) reject as noise.
  3. Initializer guides: complexity rule — try simplification first, docstring only if impossible.
- No new channels, no interruptions — everything through the existing review cycle.

## v2.3.0 — 2026-11-03

*Note: backfilled on 2026-11-04 from the GitHub release notes — the original CHANGELOG entry was missing.*

Tightened no-comments rule.

### Fixed

- Real-world feedback: agents stopped inline comments but started writing verbose docstrings.

### Changed

- Universal rule #1 now precise: only technically necessary annotations (static analysis types, tooling constructs); docstrings limited to contract info (invariants, invisible side effects); "if removing it changes nothing — remove it".
- New universal rule #2: explicit linter/static-analysis suppression ban (`@psalm-suppress`, `@ts-ignore`, `eslint-disable`, bare `except:`, etc.) — fix the root cause, never silence the checker.
- Tech-writer task template: docstring noise checklist item added.
- Code-review: docstring verbosity check added.

## v2.2.3 — 2026-11-03

*Note: backfilled on 2026-11-04 from the GitHub release notes — the original CHANGELOG entry was missing.*

Skill description: English primary.

### Fixed

- Skill description now starts in English (international default); Russian trigger phrases kept as a compact reference at the end for bilingual skill matching.

## v2.2.2 — 2026-11-03

*Note: backfilled on 2026-11-04 from the GitHub release notes — the original CHANGELOG entry was missing.*

Icon fix (PNG, marketplace.json).

### Fixed

- Plugin icon now displays: converted SVG to PNG (128×128) — ZCode marketplace requires PNG.
- Icon placed at `assets/zcode-pipeline/icon.png` (standard marketplace path).
- Icon URL set in `marketplace.json` (not `plugin.json`) — matching how official plugins reference icons.

## v2.2.1 — 2026-11-03

*Note: backfilled on 2026-11-04 from the GitHub release notes — the original CHANGELOG entry was missing.*

Plugin icon; README_CN.md rename.

### Added

- Plugin icon (SVG conveyor belt: brief → build → ship).

### Changed

- `README.zh.md` renamed to `README_CN.md` (community catalog requirement: bilingual docs as README.md + README_CN.md).

## v2.2.0 — 2026-11-03

*Note: backfilled on 2026-11-04 from the GitHub release notes — the original CHANGELOG entry was missing.*

Hooks fix and version sync.

### Fixed

- Duplicate plugin hooks warning: removed the explicit `hooks` key from `plugin.json` — ZCode auto-discovers `hooks/hooks.json` at the standard path; the double registration caused the warning.
- Version desync: manifest version now bumped before tagging (was stuck at 2.1.0 while tag v2.1.1 existed).

### Added

- Process rule: bump `version` in `plugin.json` and `marketplace.json` BEFORE creating the git tag.

## Releases — 2026-11-03

- All 9 versions (v1.0 → v2.1.1) now have GitHub Releases with titles and
  change summaries. Future releases must create a Release, not just a tag:
  `gh release create vX.Y.Z --title "vX.Y.Z — Title" --notes "Summary"`.
- READMEs (EN/RU/ZH): release creation step added to the update cycle.

## CI — 2026-11-03

Automatic prompt-lint enforcement.

### Added

- **GitHub Actions CI** (`.github/workflows/lint.yml`): runs `validate_prompts.py`
  on every push and pull request — broken prompts fail the build for everyone,
  including fork contributors.
- **Pre-commit hook** (`scripts/hooks/pre-commit`): blocks committing broken
  prompts locally. Install once: `git config core.hooksPath scripts/hooks`.
- READMEs (EN/RU/ZH): CI and hook installation documented in the update cycle.

## v2.1.0 — 2026-11-03

Bundle removed; git-marketplace is the sole install channel. Prompt linter preserved.

### Changed

- Removed `zcode-pipeline-bundle.md` and `scripts/build_bundle.py` — the fallback
  install channel is no longer needed (git-marketplace installation is confirmed
  working). One source of truth, one install path.
- `scripts/validate_prompts.py` — extracted from the bundle builder: checks mandatory
  agent sections (escalation, gross violations, verdict formats, language rule),
  personal-data leaks, and component file existence. Run after any prompt change.

### Removed

- `zcode-pipeline-bundle.md` (161KB generated artifact, prone to desynchronization).

## v2.0.0 — 2026-11-03

English Core: all agent system prompts, the coordinator skill and commands translated to
English; the project is now fully international. Validated by paired RU-EN review and a
full 13-probe self-test run.

### Added

- **Language rule** in every agent + the skill: system prompts are English; communication
  and conveyor artifacts follow the user's language (messages / project AGENTS.md); fixed
  protocol tokens and verdicts are never translated. Verified live: EN dispatches produced
  Russian-language task files in the Russian project, with English protocol tokens intact.
- `assets/AGENTS-template.md`: English template extracted from the translated initializer
  baseline ({SALUTATION}/{LANGUAGE} placeholders; ru personalization examples kept).

### Changed

- 13 agent prompts + `skills/pipeline/SKILL.md` + 5 commands translated to English
  (canonical glossary: Question round, Final brief, Track, Profile, Gross violations,
  Applicable rules, Acceptance criteria, Bridge, Knowledge base, Flow profiles...).
- Terminology canonicalized after a paired RU-EN review (14 CLEAN / 5 MINOR / 0 CRITICAL;
  all MINOR were cross-translator drift: Briefer/Developer/Technical Writer role names,
  "## Spend" section): role names now equal agent names everywhere.
- `build_bundle.py`: EN linter markers (incl. a new check that the language rule block is
  present in every agent); EN ROLES; bundle header/install text in English. Bundle size
  161KB vs 240KB (-33%) — a standing token saving on every agent call.
- `plugin.json` / `marketplace.json`: v2.0.0, English descriptions.
- `commands/pipeline-status.md` + skill + tech-writer: the task status-line label
  `**Status:**` is a fixed protocol token (kept in English in user-language tasks);
  /pipeline-status accepts legacy localized labels as a fallback.
- READMEs: English Core note (EN/RU/ZH + brief).

### Validation

- Full self-test on the English prompts: 13/13 PASS (see the run report); the language
  rule and artifact localization verified live; the self-test itself caught the status-label
  localization regression, fixed in this release.

## v1.5.0 — 2026-11-03

Fast-track profile: a cheap path for small changes — deliberately not a "skip stages" mechanism.

### Design rationale

Arbitrary skip markers were considered and rejected: they cascade through stage gates (every
agent would have to accept "stage skipped" as valid input), erode process discipline, hurt
auditability and do not even reduce cost meaningfully. Named flow profiles do: the analysis
track already proved the pattern; fast-track completes it.

### Added

- **Flow profiles** (pipeline skill): full (default) | fast-track | analysis. Profile choice
  is explicit and confirmed by the user — never a silent skip.
- **Fast-track**: Briefer → Developer → Code review (→ Security review as a second gate on
  risk triggers: crypto/secrets, user input, file paths, network, dependencies, auth) →
  coordinator commit tagged `fast-track`. Budget 1M tokens. Smallness criteria (1–2 files,
  no new contracts, no architectural decisions, reversible, <2h) checked by the Briefer,
  which proposes the profile and emits a mandatory "Fast-задача" mini-task section
  (scope/files/acceptance criteria) — no Tech Writer needed.
- **Never-cut guarantees**: brief, developer Phase 0, at least one full review (to APPROVE),
  commit only after approval.
- **Profile escalation**: developer or reviewer smelling architectural scale escalates —
  the task moves to the full conveyor with the brief already done (task file migrates from
  `_fast/` to the epic folder).
- **`/fast` command**; task files land in `.ai/tasks/_fast/{date}-{slug}.md` with statuses
  `created → implemented → fast-accepted`.
- `briefer`: smallness criteria, `**Профиль:**` brief field, "Fast-задача" section rules.
- READMEs (EN/RU/ZH + brief): /fast command, "Fast track" section with the profiles table
  and the anti-skip rationale.

## v1.4.0 — 2026-11-03

Full-coverage self-testing, analysis-to-development bridge, budgets, multi-epic.

### Added

- **Full self-test**: `/self-test` now runs 13 probes covering every agent (added:
  developer run from a sandbox task, QA gate before reviews, goal-review verdict format,
  analyst synthesis with [verified]/[hypothesis] and bridge-brief, tech-lead feasibility
  format, initializer questions-only mode, summarizer over a prepared mini-epic trail).
  Waves of parallel probes; spend of the run is reported.
- **Bridge-brief**: the analyst saves a ready `.ai/briefs/{slug}-draft.md` for findings
  that are ready to become an epic — after an analysis, the conveyor starts in one step
  (Briefer confirms the draft with the user).
- **Epic token budgets**: state files carry a budget (default 5,000,000) and accumulated
  spend; the coordinator warns at 70% and stops to ask at 100%.
- **`/pipeline-status` command**: live summary — active epic(s), stage, next step, open
  cycles, unfinished tasks, manual-checklist items, recent metrics.
- **Multi-epic**: per-epic state `.ai/state/{epic}.md` + `.ai/state/QUEUE.md`; one active
  epic, switching only at stage boundaries; legacy single state.md is migrated on first
  update; the SessionStart hook now lists all state files and the queue.
- **Guides freshness**: on re-init the initializer checks each guide's "actual on" date;
  guides older than 90 days get a full practice re-verification and an explicit
  "refreshed as stale" note in the summary.

### Changed

- README (EN/RU/ZH + brief): /self-test is 13 probes; /pipeline-status documented;
  Reliability sections extended with budgets, multi-epic and the bridge-brief.

## v1.3.0 — 2026-11-03

Reliability, speed and self-testing release (all eight improvement proposals accepted).

### Added

- **Epic state + SessionStart hook**: `.ai/state.md` (stage, next step, open cycles,
  escalations, token usage log, task statuses) updated by the coordinator after every step;
  the plugin now ships `hooks/hooks.json` + `hooks/session-start.sh` that remind about
  unfinished conveyor work at session start.
- **`/self-test` command**: regression test of the conveyor itself — six agent-contract
  probes on a sandbox fixture (`random`-based token generator): briefer round format,
  architect/manager missing-input gates, security/code review verdict formats (security
  expected to catch `random`), tech-writer task template. PASS/FAIL report to
  `.ai/self-test-{date}.md`.
- **Prompt linter** in `build_bundle.py`: mandatory sections per agent (escalation protocol,
  gross violations, verdict formats, analysis-track sections) — build fails on a broken prompt.
  Commands are now discovered from the commands directory (self-test included automatically).
- **Parallelism rules** in the `pipeline` skill: DAG-independent tasks run concurrently;
  security-review ∥ goal-review, code-review after both.
- **Epic branches**: `epic/{name}` per development epic, merged into `main` after ACCEPTED.
- **Usage metrics**: coordinator logs per-stage token usage into state; summarizer reports
  it ("Расход") and appends per-epic lines to `.ai/metrics.md`.
- **Feedback loop**: summarizer REPORT gains "Уроки и правила-кандидаты" — recurring review
  findings become concrete guide-edit proposals (applied only via re-init/user consent).
- **security-review**: WebFetch/WebSearch tools — dependency versions and CVEs are now
  checked live instead of "when information is available".

### Changed

- security-review / goal-review descriptions reflect parallel review scheduling.

## Documentation — 2026-11-03 (commands & analysis track)

- All README versions gained dedicated "Commands" and "Analysis track" sections:
  `/init-project` and `/analyze` described in full (inputs, behavior, idempotency),
  the analysis flow diagram (brief → parallel expert audits → verified synthesis →
  bridge), quality control ([verified]/[hypothesis]) and knowledge-base registration.
- Quick-start blocks extended with `/analyze` examples (EN/RU/ZH).

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
