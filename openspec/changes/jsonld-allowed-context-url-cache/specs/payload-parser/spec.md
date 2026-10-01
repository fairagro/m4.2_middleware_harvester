## ADDED Requirements

### Requirement: ParserConfig carries optional allowed_context_url

The system SHALL expose optional `allowed_context_url` on the repository sibling `parser:` / `ParserConfig` model. Both
`parser.type: jsonld` and `parser.type: html_jsonld` SHALL apply the shared JSON-LD context-loader policy keyed by that
field (see `jsonld-context-loader`). Other parser types MAY ignore the field.

#### Scenario: Field accepted on parser block

- **WHEN** a repository sets `parser: { type: html_jsonld, allowed_context_url: "https://schema.org/" }`
- **THEN** configuration validation succeeds and the Html JSON-LD parser uses that allowlisted URL

#### Scenario: Ignored by non-JSON-LD parsers

- **WHEN** a repository sets `parser.type` to a non-JSON-LD parser with `allowed_context_url` present
- **THEN** configuration validation still succeeds and that parser ignores the field
