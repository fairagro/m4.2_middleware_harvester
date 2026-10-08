# Spec Delta

## ADDED Requirements

### Requirement: Mapping docs MUST state the source placeholder contract

Each mapping document under `docs/mappers/` whose DataMapper or parser drops source-supplied placeholders MUST have a
`Source placeholders` section naming the config field (`inspire.placeholders` or `mapper.placeholders`), the fields the
check applies to, and what happens to a matching value (absent, default kept). The section MUST NOT list per-RDI
placeholder strings; those belong to the deployment config.

#### Scenario: Generator input covers placeholders

- **WHEN** a contributor reads `docs/mappers/schemaorg.md` as generator input
- **THEN** its `Source placeholders` section states that values matching `mapper.placeholders` are treated as absent,
  including the licence

#### Scenario: Per-RDI strings stay in config

- **WHEN** a new RDI needs another placeholder string
- **THEN** only its repository config changes, not the mapping document
