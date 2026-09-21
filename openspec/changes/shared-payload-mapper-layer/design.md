## Context

See `proposal.md`. Today Schema.org and Regal mappers live under
`middleware.linked_data.linked_data_mapper`, use call-scoped `StableGraph` /
`_*Run`, and are selected via plugin-local `payload_type`. Repository config
allows exactly one plugin key and has no sibling `mapper:` block. Explore
lock-ins (2026-09-15) originally chose a hard cut; revised (2026-09-16): canonical
`mapper.type` with a **deprecated** `linked_data.payload_type` lift; **one change**
moving the whole mapper package, tasks staged.

## Goals / Non-Goals

**Goals:**

- Introduce `middleware/payload` as home for `PayloadKind`, `ParsedPayload`,
  `DataMapper`, and the full RDF stack (`LinkedDataMapper`, `StableGraph`,
  Schema.org, Regal).
- Wire repository `mapper:` beside plugin config with kind compatibility checks.
- Keep linked_data Sitemap/Dataset behaviour; only change mapper ownership and
  config wiring.
- Preserve StableGraph concurrency: wrap is call-scoped, never stored on the
  shared mapper instance.
- Accept legacy `linked_data.payload_type` with a `logger.warning`, lifting it
  to `mapper.type` so existing operator YAML keeps working.

**Non-Goals:**

- Generic Protocol/PayloadParser (#141), OAI-PMH (#142), INSPIRE mapper (#143),
  additional `PayloadKind`s.
- Permanent dual vocabulary — `payload_type` is transitional only.

## Decisions

### Package name `middleware.payload`

**Choice:** Name the shared package `payload`, not `mapping`.

**Reasoning:** Intermediate-format types and later shared parsers belong beside
mappers; `payload` names the contract layer. Unchanged from PR #162 design.

### PayloadKind alignment (not inheritance)

**Choice:** Producers declare `produces: PayloadKind`; mappers declare
`accepts: PayloadKind`; config validation requires equality.

**Reasoning:** Independent replaceability; fail-fast on illegal pairs. v1 only
`rdf_graph`.

### Repository `mapper:` beside plugin; deprecate `payload_type`

**Choice:** Add `mapper:` (at least `type`) on repository entries that use
shared RDF mappers (`linked_data`). Keep `payload_type` on the linked_data
plugin `Config` model as `Field(deprecated=True)`. When set, lift it to
`mapper.type` in `RepositoryConfig` with a `logger.warning`. If both are set
and differ, validation fails. INSPIRE entries do not require `mapper` in v1.

**Reasoning:** Canonical config is `mapper.type`, but the deprecated alias must
remain a real Pydantic field (schema, ConfigWrapper, validation). Operator-facing
deprecation uses `logger.warning` (not only `DeprecationWarning`). Exactly-one-plugin
rule MUST exclude the `mapper` key.

**Alternatives considered:** Drop the field and only accept raw YAML via a
before-validator (rejected — not visible on the model); hard cut with no alias;
require `mapper` on every repository including inspire (premature until #143).

### Full package move in one change (staged tasks)

**Choice:** Move entire `linked_data_mapper/` (including `stable_graph`) into
`middleware.payload` in this change; order tasks scaffold → contracts → move →
config → plugin wiring (explore lock-in 3).

**Reasoning:** Avoids a zombie empty `payload` package on `main`; satisfies
#140 AC in one PR; StableGraph risk is the move itself, not reduced by a
contracts-only slice.

### linked_data Dataset remains the RDF producer in v1

**Choice:** No shared `PayloadParser` ABC here; `Dataset.to_graph()` builds the
graph; plugin wraps/passes into shared mapper / `ParsedPayload` as needed.

### Workspace layout

**Choice:** New uv workspace member `middleware/payload`; `linked_data` and
`harvester` depend on it. `middleware.payload` MUST NOT import
`middleware.linked_data` or `middleware.inspire`.

## Risks / Trade-offs

- **[Risk] Import / test churn** → Mitigate with staged tasks and full linked_data
  + payload pytest in validation; update MYPYPATH / quality overlays.
- **[Risk] Breaking YAML** → In-repo examples use `mapper.type`; legacy
  `payload_type` lifts with a deprecation warning until removal.
- **[Risk] Concurrency regression** → Keep `map_graph` → `_stable_wrap` →
  `_map_graph` / `_*Run` pattern; no `StableGraph` on `self`.
- **[Risk] Spec drift on requirement titles** → Refresh deltas against current
  main specs (not blind copy of Aug PR #162 text).

## Migration Plan

1. Scaffold `middleware/payload` + workspace deps.
2. Add contracts + registry.
3. Move mapper package; fix imports.
4. Add `RepositoryConfig.mapper`; keep deprecated plugin-field `payload_type`; lift legacy
   `payload_type` → `mapper.type` with deprecation; migrate in-repo YAML.
5. Wire linked_data plugin; run quality/tests.
6. Archive merges principles + domain specs.

## Open Questions

None blocking; explore lock-ins B + 3 are decided.
