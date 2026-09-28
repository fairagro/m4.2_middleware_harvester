# Shared Parsing

## Purpose

Cross-plugin ownership of discovery-unit types and the PayloadParser registry in a dedicated `middleware.parsing`
workspace package, so protocol plugins share parsers without importing each other.

## ADDED Requirements

### Requirement: Provide a shared parsing workspace package

The system SHALL provide a `middleware.parsing` workspace package that owns the shared discovery-unit types
(`DiscoveryResult` and subclasses used across plugins), the `ParserType` registry keys, the `PayloadParser` abstraction
and registry, and registered concrete PayloadParser implementations used by more than one plugin (or intended for
reuse).

#### Scenario: Plugins resolve parsers from parsing

- **WHEN** a protocol plugin needs a registered PayloadParser by `parser_type`
- **THEN** it resolves the implementation from `middleware.parsing` without importing another protocol plugin package

### Requirement: parsing may depend on harvester and payload

The `middleware.parsing` package MAY depend on `middleware.harvester` (for polite HTTP client types and shared harvest
error bases) and on `middleware.payload` (for `PayloadKind`, `ParsedPayload`, and related contracts). It MUST NOT depend
on protocol plugin packages (`inspire`, `linked_data`, `generic`, future `oai_pmh`, …).

#### Scenario: Dependency direction

- **WHEN** module dependencies are reviewed
- **THEN** `parsing` may import `harvester` and `payload`, and does not import protocol plugin packages

### Requirement: payload and plugins stay isolated from reverse parsing edges

`middleware.payload` MUST NOT depend on `middleware.parsing`. Protocol plugins MAY depend on `middleware.parsing`.
Protocol plugins MUST NOT import each other’s modules solely to obtain parsers or discovery-unit types.

#### Scenario: No payload to parsing edge

- **WHEN** import contracts are enforced
- **THEN** `middleware.payload` has no import of `middleware.parsing`

#### Scenario: No cross-plugin parser import

- **WHEN** a plugin other than `generic` needs HTML+JSON-LD or another shared parser
- **THEN** it imports that parser from `middleware.parsing`, not from `middleware.generic`
