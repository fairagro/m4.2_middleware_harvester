# Proposal

## Why

#393: DWD (harvested from the GDI-DE catalogue) writes department names into ISO `individualName`, e.g.
`KU31 Agrarmeteorologie`, `Referat Hydrometeorologische Beratungsleistungen (KU41)` or `Zentrales Klimabüro`. They split
into a given and a family name, so the INSPIRE mapper emits fake Person contacts. The Search Hub review reports these as
Persons that are really organisations (#483).

A live harvest on 2026-10-12 of all three INSPIRE sources (BonaRes, Thünen Atlas, DWD) found `individualName` only in
DWD: 6 distinct values, all departments, none a person. A name heuristic (digits, `" - "`, acronyms, keywords) would
still miss `Zentrales Klimabüro`, and real person names to test false positives against do not exist in our sources. So
the behaviour is an explicit per-repository setting, like `placeholders` (#459), not a heuristic.

## What Changes

- `MapperConfig` gains `individual_name_is_organisation` (bool, default `false`).
- When it is `true`, the INSPIRE mapper treats every `individualName` as an organisation unit: the contact follows the
  existing path for an unparseable `individualName` (`RTH`): a role-named Investigation Comment
  `<organisationName> (<individualName>)`, or `Creator Organization` for creator roles, and no Person.
- `InspireMapper` takes the setting in its constructor (keyword-only) and reads it in `from_config`.
- The in-repo DWD examples set it.
- **Non-goals:** a name heuristic; a pattern list (possible later if a source mixes people and departments); moving the
  field to `mapper.inspire_general` (#480 does that on rebase); the deployed fizz/draven config (operator change).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `person-contact-given-name`: per-repository opt-in to treat INSPIRE `individualName` as an organisation unit.

## Impact

- `middleware/payload/src/middleware/payload/mapper_config.py`, `inspire/mapper.py` and tests
- `docs/mappers/inspire.md`, in-repo DWD config examples
