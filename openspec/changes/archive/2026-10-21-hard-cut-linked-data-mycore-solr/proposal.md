# Proposal

## Why

`linked_data.sitemap_type: mycore_solr` has been soft-deprecated since #387 (warning + docs nudge to nested
`generic.protocol.mycore_solr`). The thin linked_data shim and `SitemapType.mycore_solr` enum value still exist so
legacy YAML keeps working. Operators have had a migration window; hard removal matches the flat-generic hard cut (#383)
and closes follow-up #396.

## What Changes

- **BREAKING:** Remove `SitemapType.mycore_solr` from linked_data config and unregister / delete the `MycoreSolrSitemap`
  shim. Discovery for MyCoRe Solr MUST go only through `generic.protocol.mycore_solr`.
- Reject repository config that still sets `linked_data.sitemap_type: mycore_solr` with a clear validation error (no
  warning-only path).
- Remove harvester `warn_deprecated_linked_data_mycore_solr` and related warning copy.
- Update OpenSpec (`sitemap-mycore-solr`, `linked-data-harvesting`), design notes, tests, and commented YAML examples
  that still document the shim.

**Non-goals:** Removing the entire `linked_data` plugin key (#467). Changing `generic` `MycoreSolrProtocol` behaviour.
Removing `SitemapType.xml` / `regal_find` under linked_data. Migrating live private values outside this repo.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `sitemap-mycore-solr`: Drop linked_data shim / `SitemapType.mycore_solr` support; keep generic Protocol requirements.
- `linked-data-harvesting`: Replace soft-deprecation requirement with rejection of `sitemap_type: mycore_solr`.

## Impact

- `middleware/linked_data` config, sitemap registry, shim module, unit tests
- `middleware/harvester` RepositoryConfig warning validator + tests
- `dev_environment` / Helm commented examples that still show the deprecated linked_data mycore path
- Docs that mention the shim (`docs/linked_data_to_generic.md` if present)
