---
description: UI concept design on explicit request — this command is that request
---

Launch the `ui-designer` subagent, passing the user's request (and the design
slug, if the command was invoked with one).

Launch rules:

- Render its “## Questions for the user” blocks to me interactively
  (AskUserQuestion; multiSelect where marked; “Other” gives free input) and
  return the answers to the agent; repeat the rounds until the concept is
  accepted or the user stops the session.
- Do not launch the conveyor from this command, and do not commit: the agent
  itself does not commit — design files are working artifacts.
- After the session, show the result: concept status and the CONCEPT.md path.
