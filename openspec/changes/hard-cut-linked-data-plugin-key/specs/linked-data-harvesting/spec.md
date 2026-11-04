## ADDED Requirements

### Requirement: Reject the linked_data plugin key

The system SHALL NOT provide a harvestable `linked_data` repository plugin key. Sources formerly configured under
`linked_data` MUST use `generic` with nested `protocol` and sibling `parser` / `mapper`. Concrete discovery, parse, and
map behaviour for those sources is specified under `generic-harvesting` and the relevant protocol/parser/mapper specs
(e.g. xml sitemap, MyCoRe Solr, Regal, html_jsonld).

#### Scenario: linked_data plugin key is not available

- **WHEN** an operator configures a repository with plugin key `linked_data`
- **THEN** configuration validation fails at startup
- **AND** no LinkedDataPlugin harvest path runs

#### Scenario: Equivalent harvest uses generic

- **WHEN** a repository that previously used linked_data xml sitemap + html_jsonld is configured as `generic` with the
  corresponding nested `protocol`, sibling `parser`, and `mapper`
- **THEN** harvest yields remain observationally equivalent for successful records (same PayloadKind path into the
  shared DataMapper)

## REMOVED Requirements

### Requirement: Provide a plugin-level Config class as a Pydantic BaseModel that…

**Reason:** `linked_data` plugin package removed (#467); config lives under `generic` protocols.

**Migration:** Use `generic.protocol.*` typed configs instead of `linked_data:` plugin config.

### Requirement: Require explicit sitemap_type, dataset_type, and payload_type values. Do not infer…

**Reason:** Plugin enums and `payload_type` lift removed with the plugin key (#467).

**Migration:** Nested `protocol` type key + sibling `parser` / `mapper` under `generic:`.

### Requirement: Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…

**Reason:** `LinkedDataPlugin` removed (#467).

**Migration:** Orchestrator instantiates `GenericPlugin` for former linked_data sources.

### Requirement: Select implementations using registries for sitemap, dataset, and mapper types

**Reason:** Plugin-local Sitemap/Dataset registries removed with the package (#467).

**Migration:** Protocol registry under `generic` + shared parser/mapper registries.

### Requirement: Validate config at startup and fail fast on unsupported enum…

**Reason:** linked_data plugin enums removed (#467).

**Migration:** Unsupported `generic.protocol` / parser / mapper types fail via those packages' validation.

### Requirement: Yield HarvestedArc, HarvesterError, or SkippedRecord for every dataset outcome

**Reason:** Obligation moves with GenericPlugin (#467); covered by `generic-harvesting` / plugin contract.

**Migration:** None for operators; implementers follow generic plugin yield contract.

### Requirement: Continue harvesting remaining datasets when a dataset-level failure occurs

**Reason:** Covered by `generic-harvesting` (#467).

**Migration:** None.

### Requirement: Ensure every yielded HarvesterError and SkippedRecord reaches the orchestrator so…

**Reason:** Covered by shared plugin / orchestrator contract and `generic-harvesting` (#467).

**Migration:** None.

### Requirement: Edge case — - An empty sitemap must yield zero outputs and exit…

**Reason:** Empty discovery behaviour is owned by generic Protocols (#467).

**Migration:** None.

### Requirement: Linked-data plugin MUST pass the discovered dataset URL into Schema.org mapping

**Reason:** Mapping context wiring is owned by generic + shared mappers (#467).

**Migration:** None.

### Requirement: Linked Data plugin bounds buffered mapped ARC payloads

**Reason:** Bounded pipeline lives under `generic` (#467).

**Migration:** None.

### Requirement: Linked Data plugin stops promptly on generator close

**Reason:** Cancellation behaviour lives under `generic` (#467).

**Migration:** None.

### Requirement: Coexist with generic plugin during incremental migration

**Reason:** Soft-deprecation window closed; plugin key hard-cut (#467).

**Migration:** Reconfigure remaining `linked_data:` repositories to `generic:` before upgrade.

### Requirement: Reject sitemap_type mycore_solr under linked_data

**Reason:** Entire `linked_data` plugin key removed; MyCoRe Solr already generic-only (#396 / #467).

**Migration:** Use `generic.protocol.mycore_solr` only.
