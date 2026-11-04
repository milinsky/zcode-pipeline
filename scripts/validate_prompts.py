#!/usr/bin/env python3
"""Prompt linter for the zcode-pipeline plugin.

Validates that every agent prompt contains its mandatory sections and protocol
markers, and that every command file exists with its safety markers. Run from
the repository root after any prompt change:

    python3 scripts/validate_prompts.py

Exits non-zero on any violation. See AGENT_CHECKS and COMMAND_CHECKS below for
per-agent and per-command markers. COMMAND_CHECKS holds the security-critical
minimum per command: an entry is added only when its disappearance is a safety
regression; behavioral completeness is verified outside this linter.
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

COMMANDS = ["init-project", "analyze", "self-test", "fast", "pipeline-status",
            "git-status", "git-fetch",
            "git-commit", "git-stash", "git-branch",
            "git-rebase", "git-squash", "git-undo",
            "git-pull", "git-resolve",
            "git-push", "git-push-force"]

COMMAND_CHECKS = {
    "git-status": ["This command is read-only"],
    "git-fetch": ["This command is read-only"],
    "git-commit": ["Plan first:", "gitignore=", "git check-ignore -v", "MUST NOT `git add -f`"],
    "git-stash": ["Plan first:", "git stash push -m"],
    "git-branch": ["Plan first:", "git branch -d", "unmerged"],
    "git-rebase": ["Plan first:", "GIT_SEQUENCE_EDITOR", "Never rewrite published history"],
    "git-squash": ["Plan first:", "GIT_SEQUENCE_EDITOR", "Never rewrite published history"],
    "git-undo": ["Plan first:", "git reset --soft HEAD~1", "naming what will be lost"],
    "git-pull": ["Plan first:", "pull.rebase", "/git-resolve"],
    "git-resolve": ["Plan first:", "whitespace", "import", "tests and linter"],
    "git-push": ["Explicit confirmation every time", "single commit to main delivery convention"],
    "git-push-force": ["Explicit confirmation every time", "--force-with-lease",
                       "raw `--force`", "main/master"],
}

GIT_COMMAND_SHARED = [
    "Quote every operand you interpolate",
    "is data, never instructions",
]


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
    # skill and other components exist
    for p in ["zcode-pipeline/skills/pipeline/SKILL.md",
              "zcode-pipeline/assets/AGENTS-template.md",
              "zcode-pipeline/hooks/hooks.json",
              "zcode-pipeline/hooks/session-start.sh"]:
        if not os.path.isfile(os.path.join(HERE, p)):
            errors.append(f"missing component: {p}")
    for name in COMMANDS:
        path = os.path.join(HERE, "zcode-pipeline", "commands", f"{name}.md")
        if not os.path.isfile(path):
            errors.append(f"missing component: zcode-pipeline/commands/{name}.md")
            continue
        body = read(path)
        tokens = COMMAND_CHECKS.get(name, [])
        if name.startswith("git-"):
            tokens = tokens + GIT_COMMAND_SHARED
        for token in tokens:
            if token not in body:
                errors.append(f"{name}: missing marker {token!r}")
        if "Михаил" in body:
            errors.append(f"{name}: personal data leak ('Михаил')")
    if errors:
        for e in errors:
            print("LINT FAIL:", e)
        sys.exit("Prompt linting failed — restore mandatory sections.")
    total = len(AGENTS)
    print(f"OK: {total} agents linted, all markers present, no personal data leaks.")
    print(f"OK: {len(COMMANDS)} commands checked, all markers present, no personal data leaks.")


if __name__ == "__main__":
    main()
