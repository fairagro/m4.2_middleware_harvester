# Design

## Context

See proposal.md — Why. Today `capabilities.warn_if_server_caps_page_size` runs once in `CSWClient._connect`, reads
OWSLib `constraints["MaxRecordDefault"]`, and may log a WARNING while leaving `chunk_size` / XML page size unchanged.
Paging already follows `nextrecord` / `returned`, so harvest completeness is unaffected either way. Main-spec
`csw-harvesting` design decision 6 documents the old “report only” choice from #19.

## Goals / Non-Goals

**Goals:**

- Clamp the **effective** request page size down to a positive advertised `MaxRecordDefault` when lower.
- One INFO when clamping; no WARNING for this mismatch.
- Keep readers total (never raise from hostile capabilities shapes).
- Update unit tests and main-spec design decision 6 wording on archive/apply as needed.

**Non-Goals:**

- Config flag to restore warn-without-clamp.
- Raising page size when the advert is higher.
- Changing harvest-wide `max_records` or pagination advancement rules.
- CSW HTTP pooling.

## Decisions

1. **Clamp after XML override (effective page size)** — Resolve page size as today (`chunk_size`, then valid XML
   `maxRecords` wins for `xml_query`), then `min(page_size, advertised)` when `advertised` is a positive int below that
   size. Rationale: matches #568 lock-in; one rule for all query modes. Alternative rejected: leave explicit XML
   `maxRecords` sacred (would keep inert oversized XML pages on capping servers).

2. **Store advertised cap on the client at connect** — Keep parsing in `capabilities.py` (module already owns
   GetCapabilities readers; `csw_client` is near the pylint line ceiling). Replace warn-only with a helper that returns
   `advertised_max_records(csw)` (or keep that reader) and a connect-time clamp/log helper. `CSWClient` stores
   `_max_record_default: int | None` (or equivalent) after connect and applies `min` wherever the effective page size is
   finalized (default `chunk_size` path and `_prepare_xml_paging` result). Do not mutate `Config.chunk_size` (call-site
   overrides and tests pass explicit `chunk_size`).

3. **INFO once, no WARNING, no opt-out** — Single connect-time INFO when a clamp applies; silent when advert absent/junk
   or not binding. No config flag: product decision is permanent for this change; restore via revert or operator-tuned
   sizes.

4. **Update design decision 6 in main `csw-harvesting/design.md` during apply** — Rewrite the “do not clamp” decision to
   describe clamp-down + INFO so the living design matches the new requirement (delta specs cover requirements only).

## Risks / Trade-offs

- **[Risk] Conforming servers that honour `maxRecords` above `MaxRecordDefault` get more pages** → Accepted product
  trade-off (#568); CSW defines the value as a default, not a ceiling. Mitigation: document in design decision 6;
  operators can still set `chunk_size` / XML `maxRecords` ≤ advert.
- **[Risk] Forgetting to clamp the XML path** → Apply clamp at the single place page size is resolved for XML and at the
  default chunk path used by FES/CQL/standard.
- **[Risk] Dual logs (XML override INFO + clamp INFO)** → Accept both when both apply; clamp INFO remains at most once
  per connect.

## Migration Plan

- Deploy with normal release; behaviour change only when advert < effective page size.
- Rollback: revert the change (no feature flag).
