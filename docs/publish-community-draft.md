# Draft: Community Publishing Automation

> Status: idea, not implemented. Revisit after the first PR merge.
> PR: https://github.com/zai-org/zcode-plugins/pull/158

## Problem

Every community-catalog update requires a manual PR to `zai-org/zcode-plugins`
(copy plugin → bump marketplace version → validate → commit → push → create PR).
This is tedious and easy to forget after a release.

## Proposed solution

`scripts/publish_community.sh` — one command that:

1. Clones/updates fork of `zai-org/zcode-plugins` (`~/tmp/zcode-plugins`)
2. Copies `zcode-pipeline/` from this repo → `external_plugins/zcode-pipeline/`
3. Copies `README.md` (full EN), `README_CN.md`, `LICENSE` into the plugin dir
4. Updates `marketplace.json` entry (version from our `plugin.json`)
5. Runs their `scripts/validate.py`
6. Creates branch `chore/zcode-pipeline-v{VERSION}`
7. Commits (Conventional Commits), pushes to fork
8. Opens PR via `gh pr create` with plugin-type declaration

## Prerequisites

- `gh` CLI authenticated
- Fork exists: `milinsky/zcode-plugins`

## Usage (when implemented)

```bash
# after a release in this repo:
./scripts/publish_community.sh
```

## Alternative: GitHub Action

A workflow that triggers on release tags (`on: release`), runs the same steps
via `actions/checkout` + `gh` CLI. Fully hands-off but requires a PAT with
`repo` scope stored as a secret.

## Decision

Wait for the first PR merge. If maintainers have preferences (squash, specific
PR format, version sync rules), incorporate them into the script before
automating. Don't build automation for a process that might change.
