## Context

See proposal.md — Why. Product-local overlay workflows under `.github/workflows/` (not Devinfra sync allowlist). Sibling
callers already use:

- Feature PR: `group: feature-pr-${{ github.event.pull_request.number }}`, `cancel-in-progress: true`
- Release/pre-release: `group: ${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: false`

## Goals / Non-Goals

**Goals:**

- Land the five caller `concurrency` blocks per [#182](https://github.com/fairagro/m4.2_middleware_harvester/issues/182).

**Non-Goals:**

- Editing synced `docs/ci.md` (wait for Devinfra #76 sync).
- Changing job graphs, pins, or `detect-changes` filters.

## Decisions

1. **Match sibling group strings exactly** so fleet docs/reviews stay comparable. *Alternative:* invent harvester-only
   group names — rejected (noise).

2. **Place `concurrency` after `on:` / before `jobs:`** (and after top-level `env` when present), consistent with API /
   sql_to_arc YAML layout.

3. **`skip_specs: true`** — CI tooling adopt only.

## Risks / Trade-offs

- [Cancel-in-progress on Feature PR drops in-flight logs for superseded SHAs] → Mitigation: expected; same as siblings.
- [Serialize release runs may queue longer] → Mitigation: intentional; avoid canceling publish mid-flight.
