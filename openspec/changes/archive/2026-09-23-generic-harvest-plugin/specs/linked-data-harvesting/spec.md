## ADDED Requirements

### Requirement: Coexist with generic plugin during incremental migration

The system SHALL keep the `linked_data` plugin key and its Sitemap/Dataset
registries valid while equivalent sources migrate to `generic`. Operators MAY
point a repository at `generic` with a protocol/parser pair that preserves the
prior harvest outcomes for that source.

#### Scenario: Unmigrated linked_data repositories keep working

- **WHEN** a repository still uses `linked_data` after the generic package lands
- **THEN** harvesting continues to use LinkedDataPlugin without requiring an
  immediate config rewrite

#### Scenario: First migrated pair xml + html_jsonld via generic

- **WHEN** a repository that previously used linked_data xml sitemap +
  html_jsonld is reconfigured to `generic` with the corresponding
  `protocol_type` / `parser_type` and the same `mapper`
- **THEN** harvest yields remain observationally equivalent for successful
  records (same PayloadKind path into the shared DataMapper)
