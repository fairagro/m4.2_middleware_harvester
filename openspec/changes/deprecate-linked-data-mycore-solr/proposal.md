# Proposal

## Why

After MyCoRe Solr discovery moves under `generic.protocol.mycore_solr` (#293 / PR #385), the `linked_data` +
`sitemap_type: mycore_solr` path remains a silent shim. Operators still on that config (e.g. OpenAgrar) get no
deprecation signal before a hard cut, unlike the flat-`generic` lift which already warns.

## What Changes

- Emit a clear `logger.warning` when a repository loads with `linked_data.sitemap_type: mycore_solr`, pointing operators
  at nested `generic.protocol.mycore_solr` (with sibling `parser` / `mapper`)
- Keep shim behaviour unchanged aside from the warning (no hard fail)
- Mark the linked_data `SitemapType.mycore_solr` path deprecated in OpenSpec / field docs; canonical examples stay on
  nested generic
- Add a unit test that asserts the warning is logged
- Open a follow-up issue for eventually removing the linked_data mycore_solr registration (hard cut)

## Capabilities

### New Capabilities

<!-- none — soft-deprecation of an existing path -->

### Modified Capabilities

- `sitemap-mycore-solr`: Declare `linked_data` + `SitemapType.mycore_solr` deprecated; require a `logger.warning` on
  load; shim remains functional until a hard-cut follow-up
- `linked-data-harvesting`: Note that `sitemap_type: mycore_solr` is deprecated in favour of
  `generic.protocol.mycore_solr`

## Impact

- **Depends on:** thin linked_data shim from #293 / PR #385 (rebase or land after merge)
- **Code:** `middleware/linked_data` sitemap / config and/or `middleware/harvester` repository validation; unit tests;
  `dev_environment/config_example.yaml` (prefer nested generic example)
- **Ops:** Warning-only — existing `linked_data` MyCoRe configs keep working
- **Follow-up:** separate issue to remove `SitemapType.mycore_solr` registration (cf. #383-style hard cut)
