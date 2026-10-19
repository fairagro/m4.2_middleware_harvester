## ADDED Requirements

### Requirement: INSPIRE individualName MAY be configured as an organisation unit

`MapperConfig` SHALL provide `individual_name_is_organisation` (bool, default `false`). When it is `true`, the INSPIRE
mapper SHALL NOT emit a Person for any contact with an `individualName`. It SHALL treat the contact as an unparseable
`individualName`: a Comment named from the contact role with value `<organisationName> (<individualName>)` when
`organisationName` is present, else the trimmed `individualName`, or `Creator Organization` for creator roles,
deduplicated as for other organisation Comments. When it is `false`, contacts SHALL map as before.

#### Scenario: Department name becomes a Comment when configured

- **GIVEN** `individual_name_is_organisation` is `true`
- **WHEN** a CI_ResponsibleParty has `individualName` `KU31 Agrarmeteorologie`, `organisationName`
  `Deutscher Wetterdienst`, and role `pointOfContact`
- **THEN** the Investigation MUST include a Comment named `Point of Contact` with value
  `Deutscher Wetterdienst (KU31 Agrarmeteorologie)` and MUST NOT append a Person

#### Scenario: Department as creator becomes Creator Organization when configured

- **GIVEN** `individual_name_is_organisation` is `true`
- **WHEN** a CI_ResponsibleParty has `individualName` `Zentrales Klimabüro`, `organisationName`
  `Deutscher Wetterdienst`, and role `originator`
- **THEN** the Investigation MUST include a Comment `Creator Organization` with value
  `Deutscher Wetterdienst (Zentrales Klimabüro)` and MUST NOT append a Person

#### Scenario: Default keeps person mapping

- **GIVEN** `individual_name_is_organisation` is `false` or unset
- **WHEN** a CI_ResponsibleParty has `individualName` `Jane Doe` and `organisationName` `Acme Corp`
- **THEN** the Investigation MUST contain a Person with given `Jane`, family `Doe`, and Affiliation `Acme Corp`
