## ADDED Requirements

### Requirement: URL discovery units may carry a fetch URL

The shared URL discovery unit SHALL have an optional fetch URL naming the machine-readable payload location when it
differs from the landing page. `identifier`/`url` SHALL remain the landing page used for deduplication and as harvest
source URL. When the fetch URL is unset, consumers MUST behave as before.

#### Scenario: Landing page stays the source URL

- **WHEN** a URL discovery unit has url `https://host/receive/x` and fetch URL `https://host/api/v2/objects/x`
- **THEN** the harvested ARC's source URL is `https://host/receive/x`

#### Scenario: Unset fetch URL

- **WHEN** a URL discovery unit has no fetch URL
- **THEN** fetching parsers request its url exactly as before this change

### Requirement: Register mycore_rest protocol type

The system SHALL register `mycore_rest` as a Protocol type key under `generic.protocol`, as specified in
`openspec/specs/mycore-rest-protocol/`.

#### Scenario: Registered mycore_rest protocol resolves

- **WHEN** `generic.protocol` sets the `mycore_rest` child
- **THEN** the generic plugin constructs the MyCoRe REST Protocol implementation with `mycore_rest` settings
