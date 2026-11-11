---
description: Full conveyor regression test — 15 contract probes for all agents in a sandbox (evals)
---

Run the full conveyor regression test (agents — by their actual registry names). Sandbox `.ai/sandbox/selftest-{date}/`, delete it after the run; report to `.ai/self-test-{date}.md`. Benchmark spend for the whole run ≈1.5M tokens — record the actual figure in the report.

## Preparation

1. Fixture `.ai/sandbox/selftest-{date}/tinytoken.py` — verbatim:

```python
import random
import sys

def issue_token(length: int = 16) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print(issue_token(int(sys.argv[1]) if len(sys.argv) > 1 else 16))
```

2. Analytical brief `{sandbox}/brief.md`: epic `selftest`, `**Track:** analysis`, focus: security, status final; criterion question: “is the token generation in tinytoken.py acceptable from a security standpoint?”.
3. Mini epic trail for probe 13 in `{sandbox}/fakeproj/`: `.ai/briefs/sum-brief.md` (epic `sum`, Track: development, status final, goal “replace random with secrets in fixed.py”); `fixed.py` — a copy of the fixture but already with `secrets.choice`; `.ai/tasks/sum/01-fix-2026-11-03.md` (header with status `tested`, MUST DO “replace random with secrets”, criteria: no `import random`, has `secrets.choice` + a short execution report with verification); `.ai/qa/sum/qa-2026-11-03.md` (stub: verdict QUALITY_PASSED, 3 tests OK). No git history — this is a sandbox.

## Probes (15)

| # | Agent | Input | PASS if |
|---|---|---|---|
| 1 | `briefer` | “Need a CLI to convert CSV to JSON” | “## Question round” or “## Final brief”, no escalation; writes no brief files to disk |
| 2 | `architect` | no brief (“design X”) | `### !!! ESCALATION !!!`, Type: missing_input |
| 3 | `security-review` | brief.md + fixture (analysis track) | “# Security Review”, verdict from the set; a finding about `random` with file:line |
| 4 | `code-review` | brief.md + fixture | verdict from the set; findings with [SEVERITY] |
| 5 | `goal-review` | mini development context: fixture brief → task “random→secrets” → implemented fixed.py | “# Goal Review”, verdict from {GOAL_MET, GOAL_PARTIALLY_MET, GOAL_NOT_MET, NEEDS_CONTEXT} |
| 6 | `tech-writer` | mini decomposition (1 task "replace random with secrets", its task line carrying `**Estimate:** 1.5 h | **Escalation reserve:** +0.5 h`; output — `{sandbox}/tasks/`) | task file with sections “Phase 0”, “Applicable rules”, “Acceptance criteria”; the task's Estimate line contains “min pipeline” |
| 7 | `tech-lead` | analytical feature brief (add an --alphabet flag to tinytoken, Track: analysis) | “# Feasibility”, complexity estimate, WITHOUT creating decomposition files |
| 8 | `qa` | “epic selftest, task implemented, no reviews were run” | `### !!! ESCALATION !!!` missing_input — the “only after three reviews” gate |
| 9 | `developer` | task file from probe 6 | edits the fixture (secrets), report in the task file, status implemented |
| 10 | `initializer` | empty directory `{sandbox}/empty/` as the “project root”; instruction: “return ONLY the first question block and stop — create no files, use no web” | “## Questions for the user” with stacks and a multi-select marker; no files created |
| 11 | `manager` | no artifacts (“accept epic Y”) | `### !!! ESCALATION !!!` missing_input |
| 12 | `analyst` | brief.md + reports of probes 3–4 (save their texts to `{sandbox}/expert/security.md`, `code.md` before the call) | report with [verified] and/or [hypothesis], “## Analysis complete”, REPORT.md in `{sandbox}/analysis/` (specify this output path), bridge; if it finds conveyor-ready findings — creates a draft-brief in `{sandbox}/briefs/` |
| 13 | `summarizer` | fakeproj (epic sum, ACCEPTED confirmed by the coordinator; no git history — sandbox; project root = `{sandbox}/fakeproj/`) | “## Knowledge base updated”; `{sandbox}/fakeproj/.ai/docs/epics/sum-…/REPORT.md` exists; INDEX.md created with an epic entry; the Spend-and-time part reports the absent ledger as an honest gap — no invented time values |
| 14 | `spec-designer` | empty directory `{sandbox}/design-spec/` as the "project root" + a topic (e.g. "a CLI to convert CSV to JSON"); instruction: "return ONLY the first question block and stop — create no files (nothing under .ai/designs/), use no web" | "## Questions for the user" with options, the recommended one first; no files created anywhere under `{sandbox}/design-spec/` |
| 15 | `ui-designer` | empty directory `{sandbox}/design-ui/` as the "project root" + a topic (e.g. "a settings screen for that CSV tool"); the same instruction (no files, no web) | "## Questions for the user" with options; no files created anywhere under `{sandbox}/design-ui/` |

## Order (parallel waves)

- **Wave A:** 1, 2, 8, 11, 14, 15 (all independent; 14 and 15 create their own empty sandbox dirs at run time — the pattern of `{sandbox}/empty/`).
- **Wave B:** 3, 4, 6, 7, 10 (need the fixture/brief from Preparation).
- **Wave C:** 9 (after 6), simultaneously 5 (after preparing fakeproj fixed.py).
- **Wave D:** 12 (after 3–4, having saved their reports).
- **Wave E:** 13.

## Report `.ai/self-test-{date}.md`

A 15-row table: # — agent — PASS/FAIL — actual — mismatch. Overall PASS only at 15/15; on FAIL — quotes and an indication of what changed last (CHANGELOG). File checks (6, 9, 12, 13) — actually on disk; no-file checks (10, 14, 15) — actually verified empty. Run spend (sum of subagent_tokens) — into the report. Delete the sandbox. Commit nothing.
