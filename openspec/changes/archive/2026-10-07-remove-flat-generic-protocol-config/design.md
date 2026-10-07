# Design

## Context

See proposal.md — Why. Flat fields live on `middleware.generic.config.Config` with `lift_legacy_flat_protocol` and
conflict checks. Nested `ProtocolConfig` remains the only path after this change.

## Goals / Non-Goals

**Goals:**

- Nested-only `generic.protocol` surface
- Specs and tests match nested-only behaviour
- Clear ValidationError when operators still pass flat keys (Pydantic `extra` / missing nested protocol)

**Non-Goals:**

- Removing `jsonld_parse_threshold_bytes` on generic Config
- Removing linked_data plugin key

## Decisions

1. **Reject unknown flat keys via model fields removal** — Drop the four fields entirely so YAML keys become extra (and
   fail or are ignored per model `extra` setting). Prefer fail-closed: confirm Config `model_config` / parent behaviour;
   if extras are ignored, missing nested `protocol` already fails closed — operators who only set flat fields get the
   same “protocol required” error. Alternative: keep fields as forbidden aliases — unnecessary once removed.

2. **Delete lift validator entirely** — No partial lift. Tests that used flat form switch to nested fixtures.

3. **Keep `jsonld_parse_threshold_bytes`** — Separate deprecation; out of #383 scope.

## Risks / Trade-offs

- [Out-of-repo flat YAML breaks] → Expected **BREAKING**; changelog / PR note; docs already prefer nested.
- [Missed test still using flat] → Grep + pytest failure is the gate.

## Migration Plan

1. Operators convert flat → nested before upgrade (field mapping in `docs/linked_data_to_generic.md`).
2. Ship removal; no dual-read window beyond this PR.
