## ADDED Requirements

### Requirement: Register mods_xml parser type

The system SHALL register a PayloadParser under registry key `mods_xml`, selectable via repository `parser.mods_xml`,
with `produces` kind `mods_record`, as specified in `openspec/specs/mods-xml-parser/`.

#### Scenario: generic can compose mods_xml with mods_general

- **WHEN** a generic repository sets `parser.mods_xml` and `mapper.mods_general`
- **THEN** startup kind alignment succeeds

### Requirement: Fetching parsers honour the discovery fetch URL

PayloadParsers that fetch a URL discovery unit over HTTP SHALL request the unit's fetch URL when set and its url
otherwise. The url SHALL stay the identity used in errors and as source URL.

#### Scenario: html_jsonld with fetch URL

- **WHEN** the HTML JSON-LD parser receives a URL unit with a fetch URL
- **THEN** it requests the fetch URL and reports errors under the unit's identifier
