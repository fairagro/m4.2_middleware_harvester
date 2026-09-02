## Context

See `proposal.md` — Why. Principles today document Values, Constraints, and a Module Dependency Graph focused on orchestrator ↔ plugin ownership and INSPIRE’s client/mapper split. Linked Data now has an explicit `plugin.py` (domain wiring) → `pipeline.py` (bounded concurrency) split; that pattern is not yet stated as a project rule.

## Goals / Non-Goals

**Goals:**

- Encode domain/plumbing separation as a Value + Constraint + graph example in `openspec/specs/principles/spec.md`.
- Keep the rule reviewable (SHALL/MUST + scenarios) without mandating a specific class hierarchy.

**Non-Goals:**

- Refactoring INSPIRE or other packages in this change.
- A shared harvester-level pipeline library.
- Strict hexagonal/ports-and-adapters everywhere.

## Decisions

### 1. Principles prose + ADDED requirement (not a new capability)

**Choice:** Modify the existing `principles` capability: ADDED requirement for normative review, and update Values / Constraints / Module Dependency Graph in the Full Principles section on apply/archive.

**Reasoning:** Structure rules belong with Values/Constraints. A separate capability would duplicate the principles home.

**Alternatives considered:**

- *Cursor rule / AGENTS.md only* — weaker than OpenSpec source of truth; agents already defer to principles.
- *New `code-structure` capability* — splits foundation docs without need.

### 2. YAGNI clause in the constraint

**Choice:** Explicitly forbid promoting package-local plumbing to `middleware/harvester` until a second plugin needs it.

**Reasoning:** Matches the Linked Data extraction decision and prevents premature abstraction.

### 3. Reference Linked Data in the dependency graph

**Choice:** Add a short Linked Data block showing `plugin.py → pipeline.py` and domain edges; state that pipeline modules MUST NOT import mappers or perform mapping.

**Reasoning:** Concrete example beats abstract advice for agents. Allow type/signal imports (`DiscoveryResult`, shared error types) without treating them as domain logic.

## Risks / Trade-offs

- [Subjective “substantial”] → Mitigation: scenario focuses on queue/semaphore/TaskGroup/cancellation lifecycle blocks; reviewers use judgment for tiny helpers.
- [Over-extraction of one-liners] → Mitigation: Value says extract when plumbing obscures harvest steps, not every `asyncio` call.
- [Graph drifts from code] → Mitigation: task updates graph to match current Linked Data layout; later refactors update principles in the same change.

## Migration Plan

Docs-only: edit `openspec/specs/principles/spec.md` per tasks; archive the change into main specs. No runtime migration.
