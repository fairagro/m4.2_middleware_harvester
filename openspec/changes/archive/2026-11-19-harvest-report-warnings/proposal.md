# Proposal

## Why

Shared `RepositoryScope.record_warning` (middleware API #630, shipped in fairagro-middleware-shared) is unused by the
harvester. Structured non-fatal dataset outcomes that still produce an ARC—most visibly Schema.org title fallback
(#164)—only hit logs and ARC Comments, so operators cannot see per-RDI warning counts or entries in the harvest-report
JSON-LD. Issue #637 is the consumer wire-up.

## What Changes

- Extend `HarvestedArc` with an optional, immutable list of dataset warning messages produced during mapping
- Have `arc_stream` call `RepositoryScope.record_warning` for each warning on a yielded `HarvestedArc` (record id /
  source URL from the ARC), without changing harvested / failed / skipped counts
- Attach warnings at every structured soft outcome that still yields a successful ARC (not only title fallback)—at least
  Schema.org title fallback and Schema.org non-ISO / unparsed dates; also Regal skipped-contact and CKAN spatial
  placeholder soft paths that already `logger.warning` today
- Confirm JSON-LD report emission shows warning entries/counts via the existing shared serializer (no local report
  model)
- Depend on a shared release that already exposes `record_warning` (already on the workspace pin)

### Non-goals

- Widening the plugin `AsyncGenerator` union with a separate `HarvestWarning` yield type
- Injecting `RepositoryScope` / reporting callbacks into mappers
- Promoting infrastructure / config / HTTP-retry `logger.warning` noise into the harvest report
- Changing failed / skipped semantics or ARC Comment behaviour (Comments such as `Title Source` stay)

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvest-report`: Drive `record_warning` from warnings carried on yielded `HarvestedArc` values
- `payload`: `HarvestedArc` carries optional dataset warnings through serialization hand-off
- `schemaorg-to-arc-mapping`: Title-fallback and soft date paths MUST attach report warnings on the yielded ARC
- `regal-to-arc-mapping`: Soft contact skip MUST attach a report warning when the ARC is still yielded
- `ckanext-dcat-to-arc-mapping`: Soft spatial-extent placeholder MUST attach a report warning when the ARC is still
  yielded

## Impact

- `middleware/payload` (`HarvestedArc`, Schema.org / Regal / CKAN mappers + unit tests)
- `middleware/harvester` (`arc_stream` / reporting helpers + tests)
- OpenSpec deltas under the capabilities above; mapper docs only if existing soft-path docs mention “log only”
- Shared dependency: already provides `record_warning` — bump only if the workspace pin is older than the shipping
  release
- No plugin contract / AsyncGenerator union change; no API client changes
