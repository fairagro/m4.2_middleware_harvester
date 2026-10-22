# Design

## Context

See proposal.md — Why. Soft-deprecation (#387) leaves `SitemapType.mycore_solr`, `MycoreSolrSitemap` (thin adapter over
`MycoreSolrProtocol`), and `RepositoryConfig.warn_deprecated_linked_data_mycore_solr`. Canonical discovery already lives
under `middleware.generic.protocol.mycore_solr`.

## Goals / Non-Goals

**Goals:**

- linked_data config rejects `sitemap_type: mycore_solr` (enum / validation — no warning-only path)
- Delete shim module + sitemap registry entry; remove harvester deprecation warning helper
- Specs and examples describe generic-only MyCoRe Solr

**Non-Goals:**

- Removing `linked_data` for `xml` / `regal_find` (#467)
- Changing `MycoreSolrProtocol` behaviour or generic config shape
- Auto-migrating operator YAML outside this repo

## Decisions

1. **Remove enum value, not a custom reject validator** — Drop `SitemapType.mycore_solr`. Invalid string becomes a
   normal Pydantic/enum ValidationError. Optional: keep a short custom message via `BeforeValidator` or field
   description — prefer plain enum removal unless tests need friendlier copy pointing at `generic.protocol.mycore_solr`.
   Alternative: keep the enum and fail in a model validator — rejected; dead enum values invite accidental re-use.

2. **Delete shim + registration** — Remove `middleware/linked_data/.../sitemap/mycore_solr.py` (or equivalent) and its
   registry import side-effect. linked_data sitemap factory then only knows `xml` and `regal_find`. Alternative: leave
   an unregistered stub that raises — rejected; dead code.

3. **Remove warning path entirely** — Delete `warn_deprecated_linked_data_mycore_solr`, the constant warning string, and
   tests that assert the warning. Replace with a test that `sitemap_type: mycore_solr` fails config load. Alternative:
   keep warning for one more release — rejected; this change _is_ the hard cut.

4. **Docs / examples** — Strip commented deprecated linked_data mycore_solr blocks from `config_example.yaml`; update
   `docs/linked_data_to_generic.md` and `openspec/specs/sitemap-mycore-solr/design.md` shim wording when applying
   (design.md under main specs may be edited in apply or left for archive sync — prefer update in apply tasks).

## Risks / Trade-offs

- [Out-of-repo linked_data mycore_solr YAML breaks] → Expected **BREAKING**; PR/changelog note; migration already
  documented since soft-deprecate.
- [Missed test or fixture still using shim] → Grep `sitemap_type.*mycore_solr` + pytest is the gate.
- [Confusion with generic `mycore_solr` still valid] → Error/docs must name `generic.protocol.mycore_solr` as the
  replacement, not “mycore_solr removed”.

## Migration Plan

1. Operators already on nested `generic.protocol.mycore_solr` — no action.
2. Operators still on `linked_data` + `sitemap_type: mycore_solr` — convert before upgrade (same mapping as
   soft-deprecate docs: `sitemap_url` → `protocol.mycore_solr.entry_url`, `page_size` → type settings, sibling
   `parser`/`mapper`).
3. Ship removal; no dual-read window beyond this PR.
