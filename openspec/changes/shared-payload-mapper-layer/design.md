## Context

See `proposal.md` for motivation. Today Schema.org and Regal mappers live under
`middleware.linked_data.linked_data_mapper` and are selected via plugin-local
`payload_type`. Repository config allows exactly one plugin key per entry and
has no sibling `mapper:` block. Follow-ups (#141–#143) will add a generic
protocol plugin, OAI-PMH, and INSPIRE mapper extraction; this design covers
only the shared payload + mapper extraction and config split.

## Goals / Non-Goals

**Goals:**

- Introduce `middleware/payload` as the home for `PayloadKind`, `ParsedPayload`,
  `DataMapper`, and RDF `LinkedDataMapper` implementations.
- Wire repository `mapper:` beside plugin config with kind compatibility checks.
- Keep linked_data Sitemap/Dataset behaviour; only change mapper ownership and
  config wiring.

**Non-Goals:**

- Generic Protocol/PayloadParser plugin, OAI-PMH, INSPIRE mapper move,
  additional `PayloadKind`s beyond `rdf_graph`.

## Decisions

### Package name `middleware.payload`

**Choice:** Name the shared package `payload`, not `mapping`.

**Reasoning:** Option B places intermediate-format types (`PayloadKind`,
`ParsedPayload`) and later shared parsers alongside mappers; `payload` names
the contract layer, while `mapping` understates parsers. v1 still moves mappers
first; the name anticipates #141/#143.

**Alternatives considered:** `mapping` (familiar from docs, weaker for
parsers); `to_arc` (clear destination, unusual package idiom).

### PayloadKind alignment (not inheritance between parser and mapper)

**Choice:** Producers declare `produces: PayloadKind`; mappers declare
`accepts: PayloadKind`; config validation requires equality.

**Reasoning:** Keeps parser and mapper independently replaceable while failing
fast on illegal combinations. Avoids a shared inheritance hierarchy that cannot
unify `Graph` vs future `InspireRecord` inputs.

**Alternatives considered:** Only registered (parser, mapper) pair recipes
(less flexible vs explicit `mapper:` beside protocol); runtime duck typing
without startup checks (late failures).

### Repository `mapper:` beside plugin; transitional `payload_type`

**Choice:** Add required `mapper:` on repository entries that use shared
mappers. Allow linked_data `payload_type` only as a transitional alias that
must match `mapper.type` when both appear; prefer `mapper.type` in new YAML.

**Reasoning:** Matches the orthogonal config model (protocol vs semantics)
agreed in exploration without a big-bang YAML rewrite of every example in the
same PR if aliasing eases migration—implementation SHOULD migrate examples to
`mapper.type` in this change when low-cost.

**Alternatives considered:** Keep `payload_type` inside plugin forever (blocks
cross-plugin reuse); require `mapper:` with no alias (cleaner, slightly
harsher migration).

### linked_data Dataset remains the RDF producer in v1

**Choice:** Do not introduce a shared `PayloadParser` ABC in this change;
`Dataset.to_graph()` continues to build the graph, then the plugin wraps or
passes it into the shared mapper.

**Reasoning:** Narrow scope; parser extraction belongs with the generic plugin
(#141). The plugin boundary still performs kind checks against `rdf_graph`.

### Workspace layout

**Choice:** New uv workspace member `middleware/payload` with its own
`pyproject.toml`, depended on by `linked_data` and `harvester` (for mapper
config models).

**Reasoning:** Matches existing `inspire` / `linked_data` package pattern and
keeps import boundaries enforceable.

## Risks / Trade-offs

- **[Risk] Import churn in tests** → Mitigate with clear package moves and
  updating imports in one PR; optional thin re-export shims only if needed for
  external callers (none expected).
- **[Risk] Config migration breaks demos** → Update example YAML and demo
  configs in the same change; document alias if kept.
- **[Risk] Premature abstraction** → v1 only `rdf_graph`; further kinds gated
  on #142/#143.

## Migration Plan

1. Add `middleware/payload` package and move Linked Data mappers.
2. Extend `RepositoryConfig` with `mapper`; validate kinds.
3. Update linked_data plugin wiring and YAML examples.
4. Update principles dependency graph text on archive.
5. Follow-ups remain #141–#143 (no OAI/INSPIRE mapper in this PR).

## Open Questions

None that block implementation; package name and narrow scope are decided
(`payload`, #140).
