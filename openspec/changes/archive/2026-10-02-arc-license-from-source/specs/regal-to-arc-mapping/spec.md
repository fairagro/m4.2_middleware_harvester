## ADDED Requirements

### Requirement: The ARC licence MUST come from the Regal license

`RegalMapper` MUST set `ARC.License` from the Regal `license` value (the same value as the `License` Comment) via
`middleware.payload.arc_license.license_from_value`, keeping ARCtrl's default `LICENSE` path. Without a licence the
ARCtrl default stays.

#### Scenario: Publisso licence

- **WHEN** a record has `license` `http://opendatacommons.org/licenses/by/1.0/`
- **THEN** the RO-Crate licence node text MUST be `http://opendatacommons.org/licenses/by/1.0/`
