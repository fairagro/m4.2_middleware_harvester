## Why

Plugin entrypoints increasingly mix harvest semantics (discovery, mapping, error meaning) with asyncio plumbing (queues, backpressure, cancellation). That obscures reviews and invites accidental coupling. After extracting Linked Data pipeline mechanics, we want this separation as a standing project rule—not a one-off refactor.

## What Changes

- Add a **Domain over plumbing** value to `openspec/specs/principles/`.
- Add a matching **constraint** on how plugin packages structure domain vs infrastructure modules.
- Extend the **Module Dependency Graph** with the Linked Data `plugin.py` → `pipeline.py` pattern as the reference shape.
- Non-goals: no harvester-wide generic pipeline framework; no forced rewrite of INSPIRE or other plugins in this change; no runtime behaviour change.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `principles`: Document domain/plumbing separation as a Value, Constraint, and Module Dependency Graph entry so agents and reviewers treat it as authoritative.

## Impact

- Specs only: `openspec/specs/principles/spec.md` (and optional `design.md` note if present).
- No production code required for this change; Linked Data already exemplifies the pattern via `pipeline.py`.
- Future plugin work and reviews MUST honour the new principle when growing concurrency or retry mechanics.
