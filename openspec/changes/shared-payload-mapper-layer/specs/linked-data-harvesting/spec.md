## MODIFIED Requirements

### Requirement: Require explicit sitemap_type, dataset_type, and payload_type values. Do not infer…
The system SHALL require explicit `sitemap_type` and `dataset_type` on the linked-data plugin config. Mapper selection
MUST use the repository-level `mapper.type` (shared `middleware.payload` registry). The plugin MUST NOT infer sitemap,
dataset, or mapper formats automatically. The linked-data plugin `Config` model MUST NOT expose `payload_type` as a
first-class field. Legacy repository YAML that still sets `linked_data.payload_type` MUST be accepted by lifting the
value to sibling `mapper.type` and MUST emit a `DeprecationWarning`.

#### Scenario: Satisfies — Require explicit sitemap_type, dataset_type, and payload_type values. Do not infer…

- **WHEN** linked-data plugin config omits `sitemap_type` or `dataset_type`
- **THEN** validation fails at startup; mapper selection uses repository `mapper.type` (or a deprecated
  `linked_data.payload_type` lift), not inference

#### Scenario: Explicit sitemap and dataset required

- **WHEN** linked-data plugin config omits `sitemap_type` or `dataset_type`
- **THEN** validation fails at startup

#### Scenario: Mapper comes from repository mapper config

- **WHEN** a linked-data repository is configured with `mapper.type`
- **THEN** the plugin resolves the mapper from the shared payload registry using that type

#### Scenario: Legacy payload_type is lifted with deprecation

- **WHEN** a linked-data repository sets `linked_data.payload_type` and omits `mapper`
- **THEN** validation succeeds, `mapper.type` equals the legacy value, and a `DeprecationWarning` is emitted

#### Scenario: Conflicting payload_type and mapper.type fail closed

- **WHEN** `linked_data.payload_type` and `mapper.type` are both set to different values
- **THEN** validation fails at startup

### Requirement: Select implementations using registries for sitemap, dataset, and mapper types
The system SHALL select sitemap and dataset implementations using plugin-local registries, and SHALL select mapper
implementations using the shared `middleware.payload` DataMapper registry keyed by repository `mapper.type`.

#### Scenario: Satisfies — Select implementations using registries for sitemap, dataset, and mapper types

- **WHEN** the linked-data plugin creates its mapper
- **THEN** resolution uses the shared payload package registry keyed by repository `mapper.type`

#### Scenario: Mapper registry is shared

- **WHEN** the linked-data plugin creates its mapper
- **THEN** resolution uses the shared payload package registry, not plugin-private ownership of Schema.org/Regal
  implementations

### Requirement: Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
The system SHALL implement `LinkedDataPlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the
plugin config and repository mapper config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.
The plugin MUST pass intermediate RDF graphs into the shared `LinkedDataMapper` / `DataMapper` API.

#### Scenario: Satisfies — Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…

- **WHEN** the harvester runs a linked-data repository
- **THEN** mapping is performed by a mapper instance from `middleware.payload`

#### Scenario: Plugin uses shared mapper

- **WHEN** the harvester runs a linked-data repository
- **THEN** mapping is performed by a mapper instance from `middleware.payload`
