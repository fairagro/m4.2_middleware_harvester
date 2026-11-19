# Design

## Context

See proposal.md — Why. Shared `RepositoryScope.record_warning(message, *, record_id=None, url=None)` already increments
`warned_datasets` and appends a dataset-scoped `HarvestIssue`; JSON-LD emission is owned by `JsonLdReportSerializer`.
Today `arc_stream` only routes `HarvestedArc` → submit, `HarvesterError` → fail/issue, and `SkippedRecord` → skip.
Mappers that soft-warn (Schema.org title/date, Regal unlabelled contact, CKAN spatial cap) log and/or write ARC Comments
but never reach the report.

## Goals / Non-Goals

**Goals:**

- One transport for dataset warnings: optional messages on `HarvestedArc`
- Orchestrator fans them into `record_warning` without touching harvest/fail/skip counts
- Wire every current structured soft path that still yields an ARC (inventory below)

**Non-Goals:**

- New plugin yield type or mapper→scope callbacks (rejected in explore: A2/A3)
- Report entries for infra/config/HTTP-retry logs
- Changing Comment text or fail-closed mapping rules

## Decisions

1. **Warnings live on `HarvestedArc` as `tuple[str, …]` (default `()`)** Reason: keeps the AsyncGenerator contract
   unchanged and pairs each successful map with its soft outcomes. Alternatives: separate `HarvestWarning` yield (A2 —
   widens every plugin); callback into mappers (A3 — couples payload to harvester reporting).

2. **Record warnings in `arc_stream` when the ARC is consumed, not only after `record_harvested`** Reason: mapping soft
   outcomes happened even if upload later fails; `record_warning` does not affect other counters. `record_id` / `url`
   come from `HarvestedArc.identifier` / `source_url`.

3. **Message-only payloads; shared API fixes `IssueKind.DATASET`** Reason: `record_warning` has no separate kind
   argument. Mappers phrase messages so operators can tell paths apart (e.g. title fallback vs unparsed date). No
   parallel local warning DTO beyond the string tuple.

4. **Soft-path inventory for this change (attach + keep existing log/Comment behaviour)**

   | Path                                               | Package              | Still yields ARC?     |
   | -------------------------------------------------- | -------------------- | --------------------- |
   | Schema.org title fallback (`Title Source`)         | payload schema.org   | yes                   |
   | Schema.org date normalise / `Unparsed <term>`      | payload schema.org   | yes                   |
   | Regal creator/contributor without `skos:prefLabel` | payload regal        | yes (contact skipped) |
   | CKAN spatial WKT over `spatial_extent_max_chars`   | payload ckanext-dcat | yes (placeholder)     |

5. **Accumulate warnings during map, pass into `HarvestedArc.from_arctrl(..., warnings=…)`** Reason: `from_arctrl`
   already centralizes serialization; optional kwarg avoids a second builder. Helper objects / local lists inside
   vocabulary mappers collect messages before the final `from_arctrl` call (Schema.org may need to thread a mutable list
   through `_map_investigation` / `_source_date`).

## Risks / Trade-offs

- **[Risk] Double counting if a future path both yields a warning ARC and a separate error** → Mitigation: warnings only
  on successful `HarvestedArc` yields; failures stay `record_failed`.
- **[Risk] Warning spam if every log line is promoted** → Mitigation: hard inventory above; infra logs stay logs-only.
- **[Risk] `from_arctrl` call sites forget to forward warnings** → Mitigation: default empty tuple; unit tests on each
  inventoried soft path assert non-empty `HarvestedArc.warnings`.
- **[Trade-off] Warnings recorded even when upload fails** → Acceptable: mapping quality signal is still true; counts
  remain independent.

## Migration Plan

- No config migration. Ensure workspace shared pin includes `record_warning` (already true on current main).
- Roll forward with normal harvester release; operators see new `warnings` / warned-dataset fields in JSON-LD when soft
  paths fire.
- Rollback: revert change; shared API remains unused by consumer (harmless).

## Open Questions

None — explore lock-ins A1 / all dataset soft warnings / C1 resolved.
