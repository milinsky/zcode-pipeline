---
description: Interactive specification design without the conveyor — spec-designer dialogue, accepted decisions versioned under .ai/designs/{slug}/
---

Launch the `spec-designer` subagent, passing the user's request (and the design
slug, if the command was invoked with one).

Launch rules:

- Render its “## Questions for the user” blocks to me interactively
  (AskUserQuestion; multiSelect where marked; “Other” gives free input) and
  return the answers to the agent; repeat the rounds until the design is
  accepted or the user stops the session.
- Do not launch the conveyor from this command, and do not commit: the agent
  itself does not commit — design files are working artifacts.
- After the session, show the result: design status, the DESIGN.md /
  DECISIONS.md paths, the count of accepted decisions.
