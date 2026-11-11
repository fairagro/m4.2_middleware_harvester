## ADDED Requirements

### Requirement: MODS mapper MUST follow keyword-comments contract

`ModsMapper` MUST emit Investigation keyword Comments for MODS topics/keywords according to `keyword-comments`. It MUST
NOT add a Study `Data Collection` Keywords parameter for those terms. `docs/mappers/mods.md` MUST match.

#### Scenario: MODS topics become Investigation Comments only

- **WHEN** a MODS record has topics `Soil` and `Water`
- **THEN** the Investigation MUST include keyword Comments per `keyword-comments`, and the Study MUST NOT have a Data
  Collection Keywords parameter
