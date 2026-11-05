## ADDED Requirements

### Requirement: ParserConfig exposes optional allowed_context_url on type children

The system SHALL expose optional `allowed_context_url` on JSON-LD parser type children under the repository sibling
`parser:` block (`parser.jsonld` / `parser.html_jsonld`). Both a single http(s) IRI and a list of IRIs MUST be accepted.
Matching MUST ignore trailing slashes; an `http` pin MUST also accept the same IRI under `https` (the reverse MUST NOT
hold). When unset on a JSON-LD parser type, config load MUST warn and absolute http(s) remotes MUST still be fetched via
the shared loader. Non-JSON-LD parser types MUST ignore the field.

#### Scenario: Field accepted on parser block

- **WHEN** a repository sets nested `parser.html_jsonld.allowed_context_url` to `"https://schema.org/"`
- **THEN** configuration validation succeeds and the Html JSON-LD parser uses that allowlisted URL

#### Scenario: List accepted on parser block

- **WHEN** a repository sets `allowed_context_url` under the active JSON-LD parser type child to a YAML list of http(s)
  IRIs
- **THEN** configuration validation succeeds and every payload remote must match one list entry

#### Scenario: Ignored by non-JSON-LD parsers

- **WHEN** a repository sets a non-JSON-LD parser type with `allowed_context_url` present on that child
- **THEN** configuration validation still succeeds and that parser ignores the field

## MODIFIED Requirements

### Requirement: Register PayloadParser implementations by type key

The system SHALL select PayloadParser implementations through a registry in `middleware.parsing` keyed by the active
parser type from the repository sibling `parser:` block (type-as-key child name) and SHALL reject unregistered keys at
configuration validation.

#### Scenario: Unknown parser.type fails closed

- **WHEN** the active parser type is not registered
- **THEN** configuration validation fails before harvesting starts

### Requirement: Register phenoroam_xml parser type

The system SHALL register a PayloadParser implementation under registry key `phenoroam_xml` selectable via repository
`parser` type-as-key (`parser.phenoroam_xml`), with `produces` kind `phenoroam_record`.

#### Scenario: phenoroam_xml produces phenoroam_record

- **WHEN** the active parser type is `phenoroam_xml`
- **THEN** the parser’s `produces` kind is `phenoroam_record`

#### Scenario: oai_pmh can compose phenoroam_xml with phenoroam_general mapper

- **WHEN** an `oai_pmh` repository sets nested `parser.phenoroam_xml` and nested `mapper.phenoroam_general`
- **THEN** startup kind alignment succeeds

### Requirement: Register mods_xml parser type

The system SHALL register a PayloadParser implementation under registry key `mods_xml` selectable via repository
`parser` type-as-key (`parser.mods_xml`), with `produces` kind `mods_record`.

#### Scenario: mods_xml produces mods_record

- **WHEN** the active parser type is `mods_xml`
- **THEN** the parser’s `produces` kind is `mods_record`

#### Scenario: generic can compose mods_xml with mods_general mapper

- **WHEN** a `generic` repository sets nested `parser.mods_xml` and nested `mapper.mods_general`
- **THEN** startup kind alignment succeeds

## REMOVED Requirements

### Requirement: ParserConfig carries optional allowed_context_url

**Reason:** Soft-lift of flat / `parser.type` shapes replaced by nested-only config (#478); requirement rewritten
without deprecated lift scenarios.

**Migration:** Set `allowed_context_url` under `parser.jsonld` / `parser.html_jsonld`. See the ADDED requirement
“ParserConfig exposes optional allowed_context_url on type children”.
