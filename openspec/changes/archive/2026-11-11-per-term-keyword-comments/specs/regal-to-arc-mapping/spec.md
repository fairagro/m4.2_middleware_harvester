## ADDED Requirements

### Requirement: Regal mapper MUST follow keyword-comments contract

`RegalMapper` MUST emit Investigation keyword Comments for `dcterms:subject` and optional `regal:ddc` according to
`keyword-comments`. Plain subjects without URI MUST use `keyword [<label>]` (not bare `keyword`). DDC MUST use
`keyword [DDC:<URI>]` only when a class URI is present. Aggregate `Keywords` MUST include subject labels only.
`docs/mappers/regal.md` MUST match. Study Data Collection may still list keywords as protocol parameters only if docs
explicitly keep them; this issue’s uniform SoT is Investigation Comments (prefer dropping duplicate Keywords protocol
parameter when it only mirrors Comments).

#### Scenario: Plain subject uses bracketed label name

- **WHEN** a ResearchData has a subject label `soil` with no `@id`
- **THEN** the Investigation MUST have Comment `keyword [soil]` with text `soil` and MUST NOT use bare name `keyword`
