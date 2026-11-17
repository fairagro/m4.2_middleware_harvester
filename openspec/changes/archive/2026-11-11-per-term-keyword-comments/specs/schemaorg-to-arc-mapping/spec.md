## MODIFIED Requirements

### Requirement: Study Data Collection protocol uses keywords, not description

Dataset `schema:description` SHALL map only to `Investigation.Description` and `Study.Description` — it MUST NOT be
emitted as a Data Collection parameter. Keyword terms MUST be written as Investigation Comments per `keyword-comments`
(not as a Study Data Collection Keywords parameter). The Study MUST NOT gain a Data Collection protocol table solely to
carry keywords.

#### Scenario: Keywords create Data Collection protocol

- **GIVEN** a Dataset with `schema:keywords` "soil, moisture" and a non-empty `schema:description`
- **WHEN** the mapper builds the Study
- **THEN** no "Data Collection" table exists solely for Keywords, the description appears on Investigation/Study only,
  and Investigation Comments carry the keyword contract from `keyword-comments`

#### Scenario: Description alone does not create Data Collection

- **GIVEN** a Dataset with `schema:description` but no `schema:keywords`
- **WHEN** the mapper builds the Study
- **THEN** no "Data Collection" protocol table is created

## ADDED Requirements

### Requirement: Schema.org mapper MUST follow keyword-comments contract

`GeneralSchemaOrgMapper` MUST emit Investigation keyword Comments for `schema:keywords` literals according to
`keyword-comments` (aggregate + per-term; plain labels use `keyword [<label>]`). `docs/mappers/schemaorg.md` MUST match.

#### Scenario: Plain schema keywords become per-term Comments

- **WHEN** a Dataset has keywords `Soil` and `Water`
- **THEN** the Investigation MUST include `Keywords` aggregate and `keyword [Soil]` / `keyword [Water]` Comments
