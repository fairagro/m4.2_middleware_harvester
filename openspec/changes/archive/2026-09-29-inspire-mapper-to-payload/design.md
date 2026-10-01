# Design

## Context

See `proposal.md` — Why. Today `InspireMapper` + `InspireRecord` live under `middleware.inspire`; the plugin calls
`map_record` directly with no repository `mapper:` block. Shared mappers for RDF (and other kinds) already use
`DataMapper` + sibling `mapper:` (`linked_data`, `generic`, `oai_pmh`). Import-linter forbids `payload` → `inspire`, so
moving the mapper requires moving the record models with it.

## Goals / Non-Goals

**Goals:**

- One shared `inspire_general` mapper in `middleware.payload` accepting `PayloadKind.inspire_record`
- INSPIRE plugin remains the CSW owner; maps only via registry + `MappingContext`
- Config/orchestrator parity with linked_data for mapper wiring (`(config, mapper)`; no `parser:` yet)
- Preserve ARC field behaviour covered by existing inspire mapper tests and `docs/inspire_mapping.md`

**Non-Goals:**

- Shared ISO `PayloadParser` / moving `IsoParser` out of inspire
- Defaulting `mapper.type` when omitted (explicit config only)
- Changing CSW fetch, retry, or hierarchy skip rules

## Decisions

1. **Models in `middleware.payload` (e.g. `payload/inspire/` or `payload/inspire_record/`)** Required so `DataMapper`
   can accept `InspireRecord` without importing the plugin. Optional thin re-export from `middleware.inspire.models` for
   one release is allowed if it reduces churn; prefer updating call sites to payload.

2. **`MapperType.inspire_general` + `PayloadKind.inspire_record`** Naming matches `schema_org_general` /
   `regal_general`. Kind is the intermediate discriminator; type is the registry key.

3. **API: `DataMapper[MappingContext].map(ParsedPayload, context) → Iterable[HarvestedArc]`** Plugin wraps each
   `InspireRecord` in `ParsedPayload(kind=inspire_record, value=record, identifier=…)`, sets
   `MappingContext(source_url=as_source_url(csw_record_url), harvest_source_id=record.identifier)` (http(s) only for
   `source_url`), and yields every returned `HarvestedArc` (normally one). Internals may keep today’s
   Investigation/Study/Assay builders; public surface is the shared `map` contract.

4. **Sibling `mapper:` for inspire (omission deprecated)** Canonical configs set `mapper: { type: inspire_general }`
   like other shared-mapper plugins. Omitting `mapper` is accepted with a `logger.warning` and defaults to
   `inspire_general` (same pattern as lifting `linked_data.payload_type`). Update in-repo YAML to the canonical form.

5. **Factory signature like linked_data** `InspirePlugin(config, mapper_config)` — not three-arg, because parse stays
   inside CSW/`IsoParser`.

6. **Registration** Side-effect import in a payload `register_builtin_mappers` (or inspire-specific register module
   imported from harvester config + plugin), same pattern as RDF builtins.

## Risks / Trade-offs

- **[Risk] Large move (~900 LOC models+mapper) breaks imports** → Mitigation: move models first, keep mapper tests green
  via path updates; run inspire + payload unit suites before wiring plugin.
- **[Risk] Operator configs omit `mapper:`** → Mitigation: deprecated default to `inspire_general` + warning; update
  every in-repo YAML to the canonical sibling block in the same PR; document in proposal notes.
- **[Risk] Behaviour drift during wrap** → Mitigation: keep existing mapper unit tests as the oracle; prefer move + thin
  adapter over rewrite.
- **[Trade-off] No IsoParser share yet** → Accept temporary asymmetry (inspire produces kind without shared parser);
  document follow-on for OAI+ISO.

## Migration Plan

1. Land models + kind + mapper in payload; re-point inspire imports.
2. Add config validation + orchestrator factory args; update YAML; omit-`mapper` lift with deprecation warning.
3. Switch plugin to `DataMapper.map`; delete old inspire-local mapper module (or shim that forwards once).
4. Rollback: revert PR; pre-change builds ignore sibling `mapper:`.

## Open Questions

None — lock-ins from explore (`1A`, deprecated omit-`mapper` default, `inspire_general`, shared `map`, IsoParser stays).
