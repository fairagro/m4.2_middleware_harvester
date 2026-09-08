## MODIFIED Requirements

### Requirement: Require explicit sitemap_type, dataset_type, and payload_type values. Do not infer…
The system SHALL require explicit `sitemap_type` and `dataset_type` on the
linked-data plugin config. Mapper selection MUST use the repository-level
`mapper.type` (shared `middleware.payload` registry). The plugin MUST NOT
infer sitemap, dataset, or mapper formats automatically. A deprecated
plugin-local `payload_type` field MAY be accepted only as a transitional alias
that MUST match `mapper.type` when both are present; new configs MUST set
`mapper.type`.

#### Scenario: Explicit sitemap and dataset required

- **WHEN** linked-data plugin config omits `sitemap_type` or `dataset_type`
- **THEN** validation fails at startup

#### Scenario: Mapper comes from repository mapper config

- **WHEN** a linked-data repository is configured with `mapper.type`
- **THEN** the plugin resolves the mapper from the shared payload registry
  using that type

### Requirement: Select implementations using registries for sitemap, dataset, and mapper types
The system SHALL select sitemap and dataset implementations using
plugin-local registries, and SHALL select mapper implementations using the
shared `middleware.payload` DataMapper registry keyed by repository
`mapper.type`.

#### Scenario: Mapper registry is shared

- **WHEN** the linked-data plugin creates its mapper
- **THEN** resolution uses the shared payload package registry, not a
  plugin-private mapper-only ownership of Schema.org/Regal implementations

### Requirement: Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
The system SHALL implement `LinkedDataPlugin(Plugin)` in `plugin.py`; the
central Harvester instantiates it with the plugin config and repository mapper
config and invokes `run()` and `get_expected_datasets()` via the `Plugin`
interface. The plugin MUST pass intermediate RDF graphs into the shared
`LinkedDataMapper` / `DataMapper` API.

#### Scenario: Plugin uses shared mapper

- **WHEN** the harvester runs a linked-data repository
- **THEN** mapping is performed by a mapper instance from `middleware.payload`
