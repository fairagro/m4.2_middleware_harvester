# Spec Delta

## REMOVED Requirements

### Requirement: Generic repositories use nested protocol config with deprecated flat lift

**Reason:** Flat `protocol_type` / `sitemap_url` / `http` / `page_size` lift is removed (#383); nested `protocol:` only.

**Migration:** Configure `generic.protocol` with shared `http` and exactly one type-named child (`entry_url` when
applicable).

## ADDED Requirements

### Requirement: Generic repositories use nested protocol config

Each `generic` repository entry MUST supply protocol settings as a nested `protocol` object (shared `http` plus exactly
one registered type-named child with type-specific fields such as `entry_url` when applicable). Flat `protocol_type`,
`sitemap_url`, `http`, and `page_size` on the generic plugin config MUST NOT be accepted. The repository `source_url`
for generic entries MUST resolve to the active type child's `entry_url` when that field is present, and MAY be unset
when the active type has no entry URL.

#### Scenario: Nested protocol source_url

- **WHEN** a generic repository sets `protocol.xml.entry_url` to `https://example.org/sitemap.xml`
- **THEN** repository `source_url` is that entry URL

#### Scenario: Flat protocol fields rejected

- **WHEN** a generic repository sets only flat `protocol_type` and `sitemap_url`
- **THEN** configuration validation fails
