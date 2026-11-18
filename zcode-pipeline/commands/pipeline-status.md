---
description: Conveyor status — active epic(s), stages, unclosed tasks, open loops, spend against budget
---

Show the conveyor status in this project (read-only; launch nothing and change nothing):

1. Coordination state: `.ai/state/coordination.md` (if it exists) — mode, active work (epic, stage, next step) or the last completed item, and the latest events.
2. State files: `.ai/state/*.md` (and the legacy `.ai/state.md`, if present) — for each: epic, track, branch, current stage, next step, open loops, escalations, spend vs budget.
3. Epic queue: `.ai/state/QUEUE.md` (if it exists).
4. Unclosed tasks: `grep -l -E '^\*\*(Status|Статус):\*\* \(created\|in_progress\|implemented\|reviewed\|tested\)' .ai/tasks/*/*.md` — as a list with statuses.
5. Manual remainder: open items of `.ai/docs/manual-checklist.md`.
6. Metrics: the last 3 lines of `.ai/metrics.md` (if it exists).

Answer format: a compact summary for each active/queued epic + a common “debts” section (unclosed tasks, manual remainder). If nothing is found — say so (“the conveyor is not active in this project”). + the coordination state line when the file exists (mode, active/last completed, latest events).
