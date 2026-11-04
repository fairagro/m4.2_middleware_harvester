# Design

## Context

See proposal.md — Why. OpenAgrar today: `generic` → `mycore_solr` → `html_jsonld` → `schema_org_general`. Target:
`mycore_rest` → `mods_xml` → `mods_general`, reusable for other MyCoRe RDIs.

## Goals / Non-Goals

**Goals:** REST list + object fetch; MODS extract; ARC map; fixture/example config; specs + `docs/mappers/mods.md`.

**Non-Goals:** `modified_after` harvest state; infra overlay cutover; removing `mycore_solr` from the product.

## Decisions

1. **Record URL = REST object URL** — Yield `…/api/v2/objects/{id}` (or same host path derived from `entry_url`), never
   `/receive/{id}`. Parser fetches that URL for object XML.

2. **Paging = `after_id` primary** — Prefer cursor paging documented by MyCoRe REST (`after_id` from last id on the
   page). Fall back to `offset` only if needed for a fixture/server that lacks cursor support; document the chosen
   contract in the protocol config/tests.

3. **Payload model** — Introduce `PayloadKind.mods_record` with a small structured model (or typed XML-backed view)
   sufficient for `mods_general`. Prefer a Pydantic domain model over raw ElementTree in the mapper (parser may keep
   ElementTree briefly during extract).

4. **XML hardening** — Reuse the process-default hardened lxml parser from csw-xml-hardening (no second parser policy).

5. **robots.txt** — Do not force `respect_robots_txt: false` in protocol code. Operators keep default `true` when
   `/api/` is allowed; OpenAgrar overlays adjust only if cluster checks prove otherwise.

6. **Fixtures** — Extend `dev_environment/fixtures/openagrar` with static list XML + object XML under `/api/v2/objects/`
   paths (or a sibling fixture tree) so demo/config_example can run without live OpenAgrar / PoW.

7. **Parity bar** — Compare ARC from old HTML path vs MODS path on shared sample ids in unit/fixture tests; live ~933
   run remains an acceptance check outside unit CI.

## Risks / Trade-offs

- [API shape drift across MyCoRe versions] → Keep list/object parsing defensive; pin OpenAgrar fixtures from live
  captures already used in README.
- [Mapper incomplete vs schema.org] → Explicit field list in `docs/mappers/mods.md`; expand in follow-ups, not block
  cutover.
- [Cluster still PoW on `/api/`] → Operator config / WAF follow-up; not a code block for the REST path itself.

## Migration Plan

1. Ship protocol/parser/mapper + fixture config.
2. Operators switch OpenAgrar repository YAML to the new triple.
3. Separate infra PR removes Solr/`html_jsonld`/`respect_robots_txt: false` once validated in prod.
