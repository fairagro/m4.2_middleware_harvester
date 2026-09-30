# Proposal

## Why

Generic protocol settings currently sit flat on plugin `Config` (`protocol_type`, `sitemap_url`, `http`, `page_size`),
mixing shared transport concerns with type-specific discovery settings and overloading `sitemap_url` for non-sitemap
entry points. Operators and implementers need a clear ownership boundary: shared protocol fields vs type-keyed settings,
without a redundant `type` + type-named nested block.

## What Changes

- Introduce a nested `generic.protocol:` block:
  - Shared: `http` (and future cross-protocol transport fields)
  - Type-as-key discriminator: exactly one of `xml:` / `mycore_solr:` (etc.)
  - Type-specific: `entry_url` (rename of `sitemap_url`), plus `page_size` only where pagination applies (`mycore_solr`)
- Protocol constructors take the concrete type settings model (no `SupportsSitemapUrl` typing.Protocol)
- Keep the flat tree (`protocol_type`, `sitemap_url`, `http`, `page_size` on `generic`) as **deprecated**: accept with
  warning and lift into `protocol:`
- Update specs for harvest-protocol, generic-harvesting, sitemap-mycore-solr, and harvester-configuration
- **Non-goals:** migrating `mapper:` / `parser:` to type-as-key (follow-up issue); redesigning linked_data flat config
  (shim adapts `sitemap_url` → type settings only); removing the deprecated flat tree in this change

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvest-protocol`: Protocol selection and config ownership via nested `protocol:` type-as-key; drop structural
  typing.Protocol config view
- `generic-harvesting`: Canonical `generic.protocol` shape; deprecated flat lift
- `sitemap-mycore-solr`: `entry_url` + type-local `page_size` under `protocol.mycore_solr`
- `harvester-configuration`: Document nested protocol config and deprecation lift for generic repositories

## Impact

- `middleware/generic` config, Protocol ABC/impls, plugin wiring, tests
- linked_data `MycoreSolrSitemap` shim constructs type settings from flat linked_data config
- Example/demo YAML MAY keep deprecated flat keys (still valid); at least one example SHOULD show the new shape
- Follow-up GitHub issues: (1) remove deprecated flat protocol config; (2) apply the same type-as-key pattern to
  mapper/parser (and similar)
