# mods-xml-parser Specification

## Purpose

Shared PayloadParser that fetches a MyCoRe object XML document and extracts embedded MODS into a `mods_record` payload
for the `mods_general` DataMapper.

## Requirements

### Requirement: Provide a mods_xml PayloadParser

The system SHALL provide a shared PayloadParser in `middleware.parsing`, selectable by registry key `mods_xml`, that
accepts a URL discovery unit, fetches the MyCoRe object XML via `NiceHttpClient`, extracts the `mods:mods` subtree (or
equivalent MODS root under the MyCoRe metadata container), and returns `ParsedPayload` with `kind` `mods_record`.

#### Scenario: REST object URL parses to mods_record

- **WHEN** a discovery URL returns well-formed MyCoRe object XML containing `mods:mods` and `parser` type is `mods_xml`
- **THEN** parse succeeds with `ParsedPayload.kind == mods_record` and a non-empty stable identifier

#### Scenario: HTTP client required

- **WHEN** `mods_xml` is invoked with `client` null
- **THEN** parse fails with a descriptive error indicating an HTTP client is required

### Requirement: Use hardened XML parsing

The system SHALL parse MyCoRe / MODS XML with the process-hardened lxml parser (no entity expansion / DTD / network
retrieval) consistent with `csw-xml-hardening`.

#### Scenario: Malicious entity expansion is not processed

- **WHEN** object XML contains external entity constructs
- **THEN** parsing does not expand external entities or retrieve remote DTDs

### Requirement: Fail closed on missing MODS

The system SHALL raise `ParserError` when the HTTP body is not usable XML, the MyCoRe envelope is missing, or no MODS
root can be extracted.

#### Scenario: Empty or non-MODS body fails the record

- **WHEN** the fetched document has no extractable `mods:mods`
- **THEN** the parser fails with a descriptive `ParserError` for that discovery unit
