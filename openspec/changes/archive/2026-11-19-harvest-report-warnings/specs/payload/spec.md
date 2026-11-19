# Spec Delta

## ADDED Requirements

### Requirement: HarvestedArc MAY carry dataset warnings

`HarvestedArc` MUST expose an immutable sequence of human-readable dataset warning messages (default empty). Mappers
that observe structured non-fatal outcomes while still producing an ARC MUST attach those messages on the yielded
`HarvestedArc`. `HarvestedArc.from_arctrl` MUST accept an optional warnings sequence and preserve it on the returned
value. Warning messages MUST NOT change ARC JSON serialization, study/assay counts, identifier, or source URL.

#### Scenario: Default empty warnings

- **WHEN** `HarvestedArc.from_arctrl` is called without warnings
- **THEN** the resulting `HarvestedArc` has an empty warnings sequence

#### Scenario: Warnings preserved alongside ARC JSON

- **GIVEN** a mapped ARC and two warning messages
- **WHEN** `HarvestedArc.from_arctrl` is called with those warnings
- **THEN** the `HarvestedArc` exposes both messages in order
- **AND** `arc_json`, identifier, and composition counts are unchanged relative to a call without warnings
