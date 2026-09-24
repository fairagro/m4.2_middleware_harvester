## Context

See proposal.md — Why. Root `pyproject.toml` already uses `--strict-markers` with `unit` / `integration` / `asyncio`.
API registers the same `system_local` / `system_external` strings Devinfra #120 will put in the synced pre-push `-m`
filter.

## Goals / Non-Goals

**Goals:**

- Register the two markers with fleet-aligned descriptions so the expression is valid here.
- Confirm whether any existing tests must be re-marked in this PR (default: none).

**Non-Goals:**

- Implementing Devinfra #120 itself (synced hook change lives upstream).
- Replacing `integration` with `system_external` fleet-wide unless a clear adopt need appears.
- Changing CI workflow marker filters in this slice.

## Decisions

1. **Copy API marker descriptions verbatim** (`system_local`: locally runnable external services / testcontainers;
   `system_external`: real external systems/secrets). _Alternative:_ invent harvester-only wording — rejected (fleet
   docs/hooks assume shared names).

2. **Do not re-mark inspire `@pytest.mark.integration` in MVP** unless audit shows they would break the post-#120
   pre-push budget and belong under `system_external`. Issue acceptance allows zero remaps; keep scope minimal.

3. **`skip_specs: true`** — pytest config / tooling adopt only.

## Risks / Trade-offs

- [After #120 sync, slow `integration` tests still run on every push] → Mitigation: follow-up issue to re-mark real-CSW
  suites as `system_external` if duration becomes a problem; not blocking marker registration.
- [Typos in marker names] → Mitigation: match API strings exactly; smoke `pytest --markers` / collect with the future
  `-m` expression.
