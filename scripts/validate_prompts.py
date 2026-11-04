#!/usr/bin/env python3
"""Prompt linter for the zcode-pipeline plugin.

Validates that every agent prompt contains its mandatory sections and protocol
markers. Run from the repository root after any prompt change:

    python3 scripts/validate_prompts.py

Exits non-zero on any violation. See AGENT_CHECKS below for per-agent markers.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AGENTS = ["briefer", "architect", "tech-lead", "tech-writer", "developer",
          "security-review", "goal-review", "code-review", "qa", "manager",
          "summarizer", "initializer", "analyst"]

AGENT_CHECKS = {
    "briefer": ["Question round", "Final brief", "Track:", "fast-track", "Final brief readiness criterion"],
    "architect": ["Design principles", "Analysis track", "Position in the pipeline"],
    "tech-lead": ["decompos", "Tech Lead's decision", "feasibility", "Analysis track"],
    "tech-writer": ["Phase 0", "Applicable rules", "Acceptance criteria", "Mandatory task template"],
    "developer": ["Phase 0", "implemented", "MUST NOT DO", "Implementation rules"],
    "security-review": ["PASS_WITH_WARNINGS", "Analysis track", "NEEDS_MORE_CONTEXT"],
    "goal-review": ["GOAL_MET", "GOAL_PARTIALLY_MET", "traceability"],
    "code-review": ["REQUEST_CHANGES", "NEEDS_DISCUSSION", "Analysis track"],
    "qa": ["QUALITY_PASSED", "QUALITY_FAILED", "Edge case checklist"],
    "manager": ["ACCEPTED", "REJECTED", "Return stage"],
    "summarizer": ["Knowledge base updated", "Lessons and rule candidates", "manual-checklist"],
    "initializer": ["source=file|embedded", "Personalization", "Determine the project state",
                    "Git hygiene", "core.excludesFile", ".git/info/exclude", "git rm --cached"],
    "analyst": ["[verified]", "[hypothesis]", "Bridge"],
}
REQUIRED_ALL = ["## Gross violations", "### !!! ESCALATION !!!", "system prompts are English"]


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main() -> None:
    errors = []
    for a in AGENTS:
        path = os.path.join(HERE, "zcode-pipeline", "agents", f"{a}.md")
        body = read(path)
        for token in REQUIRED_ALL + AGENT_CHECKS.get(a, []):
            if token not in body:
                errors.append(f"{a}: missing marker {token!r}")
        # personal data leak check
        if "Михаил" in body:
            errors.append(f"{a}: personal data leak ('Михаил')")
    # skill and commands exist
    for p in ["zcode-pipeline/skills/pipeline/SKILL.md",
              "zcode-pipeline/commands/init-project.md",
              "zcode-pipeline/commands/analyze.md",
              "zcode-pipeline/commands/self-test.md",
              "zcode-pipeline/commands/fast.md",
              "zcode-pipeline/commands/pipeline-status.md",
              "zcode-pipeline/assets/AGENTS-template.md",
              "zcode-pipeline/hooks/hooks.json",
              "zcode-pipeline/hooks/session-start.sh"]:
        if not os.path.isfile(os.path.join(HERE, p)):
            errors.append(f"missing component: {p}")
    if errors:
        for e in errors:
            print("LINT FAIL:", e)
        sys.exit("Prompt linting failed — restore mandatory sections.")
    total = len(AGENTS)
    print(f"OK: {total} agents linted, all markers present, no personal data leaks.")


if __name__ == "__main__":
    main()
