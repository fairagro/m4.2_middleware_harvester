# Design

## Context

`system_local` already discovers each `fixtures/arc_export/<rdi>/` directory and runs `validate_rocrate` on
`ro-crate-metadata.json`. Today each MVP folder holds one tiny synthetic Investigation. Active harvest RDI ids live in
`dev_environment/config.all-rdis.yaml` (bonares, edal, publisso, sradi, plabipd, openagrar-fixture, phenoroam).
OpenAgrar live (`openagrar`) remains commented there and is tracked as #614.

## Goals / Non-Goals

**Goals:**

- Prove real mapped payloads pass DataHUB-equivalent `arc-export` for each active RDI over time.
- Prefer **per-RDI** fixture folders (not one folder per technology family), because sibling RDIs diverge in the field.
- Document how each fixture file was produced and which input features it covers.
- Land shared docs/gate expectations in this change; ship the first real-data suite for **bonares**.

**Non-Goals:**

- Changing mapper / parser production behaviour except when a fixture proves an `arc-export` gap (then fix + fixture
  together).
- Harvesting every record from every RDI into git.
- Replacing the minimal smoke crates in this change (they stay as path smoke unless a later slice deliberately removes
  them).
- Implementing edal / publisso / sradi / plabipd / openagrar / phenoroam suites here (#610–#615).

## Decisions

1. **Active RDI set = `config.all-rdis.yaml` enabled entries (+ OpenAgrar live via #614).** Reasoning: that file is the
   operator-facing “can actually be harvested” inventory used for before/after runs; Helm examples alone omit
   edal/sradi/plabipd/phenoroam.

2. **Fixture layout supports multiple crates per RDI.** Reasoning: breadth needs more than one happy path. Keep
   backward-compatible discovery: either multiple `ro-crate-metadata.json` files under nested dirs
   (`<rdi>/<case>/ro-crate-metadata.json`) or clearly named siblings — prefer `<rdi>/<case-id>/ro-crate-metadata.json`
   so the existing single-file-per-dir helper can parametrize over leaf dirs. Smoke crates may remain at
   `<rdi>/ro-crate-metadata.json` **or** move under `<rdi>/smoke/` in a later tidy; this change MUST NOT break current
   parametrization without updating tests in the same PR.

3. **Generation = curated real records → real map path → commit JSON-LD only.** Reasoning: lock reproducibility without
   committing full harvest caches; redact PII/contact emails in docs when needed; use Git LFS when a crate exceeds a
   practical GitHub blob comfort threshold (call out in docs).

4. **C1 — keep minimal smoke fixtures.** Reasoning: they are tiny, always-green path checks independent of harvest
   flakiness; real-data sets are additive.

5. **Split delivery.** Reasoning: `cost:expensive` AC spans many live sources; parent #600 carries the contract +
   bonares; sub-issues own each remaining RDI suite.

## Risks / Trade-offs

- **Live source drift:** curated snapshots can go stale relative to live endpoints — accept pin-by-commit of mapped
  output; regenerate when mappers change intentionally.
- **openagrar-fixture vs openagrar:** fixture server stand-in is not live OpenAgrar; #614 owns the preferred live/MODS
  path. Do not pretend `openagrar-fixture` satisfies the OpenAgrar live AC.
- **CI time/size:** many large crates inflate clone/CI — prefer small curated sets (single-digit files per RDI) and LFS
  when needed.
- **False confidence:** breadth is judgment-based, not exhaustive enumeration of every ISO/Schema.org field — docs must
  list covered cases so gaps stay visible.
