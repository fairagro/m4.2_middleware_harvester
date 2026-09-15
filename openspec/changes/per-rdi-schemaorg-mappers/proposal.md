## Why

`#164` landed OpenAgrar's title-fallback chain (`schema:headline` →
`schema:alternativeHeadline` → HTML page title) inside the shared
`GeneralSchemaOrgMapper`, because that is where the mapping code lives. On
`#221` @Zalfsten flagged the pattern he had already raised on
`m4_rdi_portfolio#11`: one shared Schema.org mapper accumulating repository
quirks gets harder to reason about with every RDI we onboard, and it silently
weakens the base contract for RDIs that never had the quirk.

Concretely, the shared mapper today accepts a Dataset with no `schema:name` for
*every* Schema.org RDI, even though only OpenAgrar's MyCoRe export is known to
omit it. That contradicts `schemaorg-to-arc-mapping`'s "fail closed on missing
required fields" and was never spec'd.

This change introduces the per-RDI overlay mechanism (`#227`) and moves the one
piece of genuinely RDI-specific behaviour onto it, aligning with `#170`'s
`RDI mapper = base format mapper + repository-specific overrides`.

`#125` (e!DAL-PGP sibling-replicate identifier collision) is **not** part of the
move: it carries no RDI-specific code. It was already fixed on 2026-08-24 by the
harvest-stable identifier cascade (`94b8d9b`), which is RDI-agnostic — its own
spec scenarios are written against OpenAgrar payloads. Everything that landed
under `#125` in this repo (`b14cfde`, `bb46c81`) is regression tests. e!DAL-PGP
therefore keeps `payload_type: schema_org_general` and gets no overlay mapper
until a real e!DAL-only rule exists (YAGNI, `principles.md`).

## What Changes

**Overlay mechanism**

- Add an optional `mapper` field to the Linked Data plugin `Config`, a
  `LinkedDataMapper.overlay_registry` keyed by overlay name, and a `BUILDS_ON`
  declaration on each overlay. `LinkedDataPlugin.create_mapper` resolves the
  overlay when `mapper` is set and fails fast on an unknown name or a
  base/`payload_type` mismatch; absent `mapper` keeps today's behaviour exactly.
- `PayloadType` is **not** extended. It names the payload format; encoding RDI
  identity there would contradict `#140`'s protocol ≠ payload format decision
  and churn operator-visible YAML that `#140` would then have to unpick.

**Title fallback**

- Add an overridable `GeneralSchemaOrgMapper.resolve_title_fallback` hook
  returning a `ResolvedField(value, source)` or null, plus a `TITLE_SOURCES`
  class attribute naming the accepted carriers. The base returns no fallback and
  reports only `schema:name` in its error.
- **Restore** the base mapper's fail-closed behaviour on missing/blank
  `schema:name` (undoing `#164`'s widening of the shared contract).
- Add `OpenAgrarSchemaOrgMapper`, a subclass of `GeneralSchemaOrgMapper`
  registered as overlay `openagrar`, carrying `#164`'s fallback chain and
  nothing else.

**Dialect seams** (enabling Bioschemas / AgriSchema without re-opening the ABC)

- Convert `_stable_wrap` from a `@staticmethod` to an instance method, so a
  mapper's `term_namespaces` can come from the instance rather than only a
  hardcoded class body. `map_graph` already calls it as `self._stable_wrap(...)`,
  so this is call-site compatible.
- Collapse `GeneralSchemaOrgMapper.SCHEMA_URIS` into the single
  `SCHEMA_ORG_NAMESPACES` source, so Dataset type detection and term access
  cannot disagree and adding an extension namespace is one edit.

**Config and tests**

- Point the OpenAgrar harvest configs (`helm/harvester/values.yaml` examples) at
  `mapper: openagrar`; leave e!DAL and other Schema.org RDIs untouched.
- Split the RDI-specific title-fallback tests out of the shared mapper's test
  files into a per-mapper test module; keep the `#125` regression test on the
  base mapper, where the behaviour it guards actually lives.

### Non-goals

- Implementing `#170`'s `docs/mappers/` layout (docs-first, separate change).
  This change only makes the code shape match its base+overrides direction and
  adopts its `builds_on` vocabulary as `BUILDS_ON`.
- Re-litigating `#140` (shared `middleware.payload` mapper layer). The `mapper`
  key is deliberately shaped so `#140` can adopt or rename it rather than undo it.
- A `SchemaOrgProfile` object, config-driven fallback chains, or `dialects:`
  YAML — deferred until the first real dialect or `#140` lands.
- Moving the JSON-LD `@context` allowlist out of `jsonld_validation.py`'s module
  constant into a mapper-declared contribution. Real dialect blocker, but it
  crosses into the dataset layer; tracked as a separate follow-up issue.
- An `EdalPgpSchemaOrgMapper` seam with no behaviour in it.
- Migrating Regal or INSPIRE to per-RDI overlays.
- Changing the identifier cascade, `#148`'s Dataset subject selection, or any
  other genuinely RDI-agnostic rule.

## Capabilities

### New Capabilities

- `openagrar-schemaorg-overrides`: RDI overlay contract for OpenAgrar on top of
  `schemaorg-to-arc-mapping` — accepted title carriers when `schema:name` is
  absent, the `Title Source` provenance comment, and the requirement that the
  overlay changes nothing else.

### Modified Capabilities

- `linked-data-mapper`: RDI-specific Schema.org behaviour MUST live in a per-RDI
  subclass registered in a dedicated overlay registry (not keyed by
  `payload_type`) and declaring `BUILDS_ON`; the shared mapper MUST NOT branch on
  RDI identity. Adds the `resolve_title_fallback` extension point and requires
  `_stable_wrap` to be instance-scoped and single-sourced.
- `linked-data-harvesting`: adds the optional `mapper` config field, its
  fail-fast validation, and the rule that overlay selection stays explicit.
- `schemaorg-to-arc-mapping`: "fail closed on missing required fields" is scoped
  explicitly to the shared mapper, with overlay relaxation allowed only via a
  registered per-RDI mapper that records provenance.

## Impact

- Code: `middleware/linked_data/.../linked_data_mapper/` (base mapper, ABC,
  Regal `_stable_wrap` signature, new `openagrar_schema_org_mapper.py`, package
  exports), `config.py` (`mapper` field), `plugin.py` (overlay resolution), unit
  tests under `middleware/linked_data/tests/unit/`.
- Config: `helm/harvester/values.yaml` OpenAgrar examples gain `mapper:
  openagrar`. Operators harvesting OpenAgrar MUST add that line; omitting it
  restores the pre-`#164` skip of the ~13/910 records that omit `schema:name`
  (fail-closed record-level errors, no silent garbage). No existing config value
  changes meaning, and configs without `mapper` are unaffected.
- Domains: `openspec/specs/linked-data-mapper/`,
  `openspec/specs/linked-data-harvesting/`,
  `openspec/specs/schemaorg-to-arc-mapping/`, new
  `openspec/specs/openagrar-schemaorg-overrides/`.
- Tracks: GitHub `#227`; stacked on `#221` (`#164`), which must merge first.
  Feeds `#170` (`builds_on` in code) and `#140` (`mapper:` key shape).
