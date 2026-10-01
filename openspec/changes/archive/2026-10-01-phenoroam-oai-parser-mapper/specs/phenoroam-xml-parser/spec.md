# Phenoroam XML Parser

## Purpose

Shared PayloadParser that turns inline OAI-PMH `phenoroam` metadata (`pr:metadataDataset`) into a `phenoroam_record`
ParsedPayload for the PhenoRoam DataMapper.

## ADDED Requirements

### Requirement: Provide an inline phenoroam_xml PayloadParser

The system SHALL provide a shared PayloadParser in `middleware.parsing`, selectable by registry key `phenoroam_xml`
(`parser.type`), that accepts a `middleware.parsing` discovery unit carrying inline XML and returns `ParsedPayload` with
`kind` `phenoroam_record` and a structured value suitable for the `phenoroam_general` DataMapper. The parser MUST NOT
require an HTTP client when the metadata XML is already present on the discovery unit.

#### Scenario: Inline phenoroam XML parses to phenoroam_record

- **WHEN** a discovery unit supplies well-formed `pr:metadataDataset` XML and `parser.type` is `phenoroam_xml`
- **THEN** parse succeeds with `ParsedPayload.kind == phenoroam_record` and a non-empty stable identifier from the
  discovery unit or embedded `itemUUID`

#### Scenario: HTTP client may be omitted

- **WHEN** the phenoroam XML parser is invoked with inline metadata and `client` is null
- **THEN** parse does not fail solely because no HTTP client was provided

### Requirement: Fail closed on unusable phenoroam XML

The system SHALL raise `ParserError` when the inline payload is missing, empty, not `pr:metadataDataset`, or otherwise
not parseable into the intermediate record.

#### Scenario: Malformed or wrong-root XML fails the record

- **WHEN** the inline metadata cannot be parsed as `pr:metadataDataset`
- **THEN** the parser fails with a descriptive `ParserError` for that discovery unit
