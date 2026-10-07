## ADDED Requirements

### Requirement: HtmlJsonLdDataset inherits shared parser context policy

When `HtmlJsonLdDataset` (or its shim) extracts embedded JSON-LD via `HtmlJsonLdParser`, remote `@context` acceptance
SHALL follow `parser.allowed_context_url` and the shared context loader. The Dataset MUST NOT apply a separate
hard-coded Schema.org-only context allowlist that diverges from the parser policy.

#### Scenario: Dataset inherits parser allowlisted URL

- **WHEN** linked_data or generic harvest uses `html_jsonld` with `allowed_context_url` set to the page's context IRI
- **THEN** embedded JSON-LD with that remote `@context` parses successfully under the shared loader policy

#### Scenario: Dataset works when pin unset

- **WHEN** harvest uses `html_jsonld` without `allowed_context_url` and the page embeds an absolute http(s) remote
  `@context`
- **THEN** parse still uses the shared loader and does not fail solely because the field is missing; config validation
  has already warned about the unset pin
