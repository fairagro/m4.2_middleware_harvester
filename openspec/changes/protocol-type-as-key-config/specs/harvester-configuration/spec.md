## ADDED Requirements

### Requirement: Generic repositories use nested protocol config with deprecated flat lift

Each `generic` repository entry MUST supply protocol settings either as a nested `protocol` object (shared `http` plus
exactly one registered type-named child with type-specific fields such as `entry_url` when applicable) or as the
deprecated flat fields `protocol_type` and `sitemap_url` (optional flat `http` / `page_size`) that the system lifts into
`protocol` with a deprecation warning. The repository `source_url` for generic entries MUST resolve to the active type
child's `entry_url` when that field is present, and MAY be unset when the active type has no entry URL.

#### Scenario: Nested protocol source_url

- **WHEN** a generic repository sets `protocol.xml.entry_url` to `https://example.org/sitemap.xml`
- **THEN** repository `source_url` is that entry URL

#### Scenario: Deprecated flat sitemap_url still provides source_url

- **WHEN** a generic repository sets only deprecated `protocol_type` and `sitemap_url`
- **THEN** repository `source_url` equals that `sitemap_url` after lift
