## ADDED Requirements

### Requirement: Resolve Schema.org context IRIs locally

The parser SHALL replace a top-level `@context` that is exactly a Schema.org IRI (`http://schema.org`,
`https://schema.org`, with or without trailing slash), or such an IRI as an entry of a top-level `@context` list, with
the inline context `{"@vocab": "http://schema.org/"}` before parsing, and MUST NOT fetch it. Any other string-valued
`@context` / `@import` SHALL still be rejected with `ParserError`.

#### Scenario: Schema.org context string

- **WHEN** the payload's `@context` is `"http://schema.org"`
- **THEN** parse succeeds, terms resolve to `http://schema.org/` IRIs, and no network request is made

#### Scenario: Other remote context next to Schema.org

- **WHEN** the payload's `@context` is a list of `"https://schema.org"` and another URL string
- **THEN** parse fails with `ParserError`
