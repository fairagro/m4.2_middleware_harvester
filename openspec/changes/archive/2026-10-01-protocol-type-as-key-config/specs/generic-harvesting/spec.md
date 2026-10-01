## MODIFIED Requirements

### Requirement: Provide a plugin-level Config as a Pydantic BaseModel

The system SHALL provide a plugin-level `Config` class as a Pydantic `BaseModel` referenced by the main harvester
repository schema under the `generic` plugin key. Canonical protocol selection SHALL use a nested `protocol` block with
shared `http` and exactly one type-named child (`xml`, `mycore_solr`, …). The config SHALL NOT infer protocol from URLs
or payloads. Shared parser selection SHALL use the repository-level `parser:` block (not a field on the generic plugin
config).

#### Scenario: Explicit protocol and parser types required

- **WHEN** a repository entry uses the `generic` plugin key
- **THEN** validation fails closed unless a resolvable `protocol` configuration is present (nested canonical form or
  deprecated flat lift) and `parser.type` is set on the sibling `parser` block

#### Scenario: Explicit protocol type required

- **WHEN** a repository entry uses the `generic` plugin key without nested `protocol` and without deprecated flat
  `protocol_type` + `sitemap_url`
- **THEN** validation fails closed

#### Scenario: Parser selected via sibling parser block

- **WHEN** a `generic` repository is configured with `parser: { type: html_jsonld }`
- **THEN** the PayloadParser implementation is selected from repository `parser.type`

#### Scenario: Canonical nested protocol accepted

- **WHEN** a `generic` repository sets `protocol: { http: …, xml: { entry_url: … } }` and
  `parser: { type: html_jsonld }`
- **THEN** configuration validation succeeds and the XML Protocol is selected

### Requirement: Select Protocol and PayloadParser via registries

The system SHALL resolve the active protocol type key under `generic.protocol` through the Protocol registry owned by
the generic plugin package and `parser.type` through the shared PayloadParser registry in `middleware.parsing`, and
SHALL fail fast at startup on unsupported values.

#### Scenario: Unknown protocol_type fails at config validation

- **WHEN** the active protocol type key is not registered
- **THEN** configuration validation fails before harvesting starts

#### Scenario: Unknown parser.type fails at config validation

- **WHEN** `parser.type` is not registered in `middleware.parsing`
- **THEN** configuration validation fails before harvesting starts

## ADDED Requirements

### Requirement: Deprecated flat protocol fields lift into nested protocol

The system SHALL continue to accept the deprecated flat generic fields `protocol_type`, `sitemap_url`, optional `http`,
and optional `page_size`, SHALL emit a deprecation warning when they are used to supply protocol settings, and SHALL
lift them into the nested `protocol` object (`sitemap_url` becomes the active type child's `entry_url`; `page_size`
applies only for types that define it). When both nested `protocol` and flat fields are present, the system SHALL fail
closed on disagreement and SHALL warn on agreement.

#### Scenario: Flat protocol_type and sitemap_url still harvest

- **WHEN** a `generic` repository sets only deprecated `protocol_type: xml` and `sitemap_url` (no nested `protocol`)
- **THEN** validation succeeds with a deprecation warning and the XML Protocol uses `entry_url` equal to that
  `sitemap_url`

#### Scenario: Conflicting nested and flat protocol settings fail

- **WHEN** nested `protocol` selects `mycore_solr` but flat `protocol_type` is `xml`
- **THEN** configuration validation fails before harvesting starts
