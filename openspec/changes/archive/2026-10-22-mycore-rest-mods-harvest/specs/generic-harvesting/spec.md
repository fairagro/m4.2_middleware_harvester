## MODIFIED Requirements

### Requirement: Provide a plugin-level Config as a Pydantic BaseModel

The system SHALL provide a plugin-level `Config` class as a Pydantic `BaseModel` referenced by the main harvester
repository schema under the `generic` plugin key. Canonical protocol selection SHALL use a nested `protocol` block with
shared `http` and exactly one type-named child (`xml`, `mycore_solr`, `mycore_rest`, …). The config SHALL NOT infer
protocol from URLs or payloads. Shared parser selection SHALL use the repository-level `parser:` block (not a field on
the generic plugin config). Flat `protocol_type` / `sitemap_url` / `http` / `page_size` fields MUST NOT be accepted.

#### Scenario: Explicit protocol and parser types required

- **WHEN** a repository entry uses the `generic` plugin key
- **THEN** validation fails closed unless a nested `protocol` configuration is present and `parser.type` is set on the
  sibling `parser` block

#### Scenario: Explicit protocol type required

- **WHEN** a repository entry uses the `generic` plugin key without nested `protocol`
- **THEN** validation fails closed

#### Scenario: Parser selected via sibling parser block

- **WHEN** a `generic` repository is configured with `parser: { type: html_jsonld }`
- **THEN** the PayloadParser implementation is selected from repository `parser.type`

#### Scenario: Canonical nested protocol accepted

- **WHEN** a `generic` repository sets `protocol: { http: …, xml: { entry_url: … } }` and
  `parser: { type: html_jsonld }`
- **THEN** configuration validation succeeds and the XML Protocol is selected

#### Scenario: mycore_rest nested protocol accepted

- **WHEN** a `generic` repository sets `protocol: { http: …, mycore_rest: { entry_url: … } }` and
  `parser: { mods_xml: {} }` with `mapper: { mods_general: {} }`
- **THEN** configuration validation succeeds and the MyCoRe REST Protocol is selected

#### Scenario: Flat protocol fields rejected

- **WHEN** a `generic` repository sets only flat `protocol_type` and `sitemap_url` (no nested `protocol`)
- **THEN** configuration validation fails
