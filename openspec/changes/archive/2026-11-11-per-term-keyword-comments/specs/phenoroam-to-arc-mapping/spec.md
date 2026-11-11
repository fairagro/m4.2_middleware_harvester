## ADDED Requirements

### Requirement: Phenoroam mapper MUST follow keyword-comments contract

`PhenoroamMapper` MUST emit Investigation keyword Comments for phenoroam keywords according to `keyword-comments`. It
MUST NOT add a Study `Data Collection` Keywords parameter for those terms. `docs/mappers/phenoroam.md` MUST match.

#### Scenario: Phenoroam keywords become Investigation Comments only

- **WHEN** a phenoroam record has keywords `Soil` and `Water`
- **THEN** the Investigation MUST include keyword Comments per `keyword-comments`, and the Study MUST NOT have a Data
  Collection Keywords parameter
