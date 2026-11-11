## ADDED Requirements

### Requirement: InspireMapper MUST emit Assay Sensor Acquisition protocol from acquisition_information

When `InspireRecord.acquisition_information` yields at least one non-empty parameter value after mapping,
`InspireMapper` MUST add an Assay protocol table named `Sensor Acquisition` with **parameter columns only** (no invented
Input/Output Data or Sample columns). Platform labels MUST be taken from each platform’s description if non-empty, else
its identifier; instrument labels MUST be taken from each instrument’s type if non-empty, else its identifier. Multiple
labels MUST be joined with `"; "` in harvest-stable order (trim; drop empty; casefold-dedupe; sort casefold then
original). Parameter names MUST be `Platform` and/or `Instrument` when the corresponding joined value is non-empty. When
acquisition is absent or yields no parameters, the mapper MUST NOT add a `Sensor Acquisition` table. Assay
`TechnologyPlatform` MUST remain the existing hardcoded annotation in this requirement. `docs/mappers/inspire.md` MUST
describe this protocol mapping.

#### Scenario: Acquisition present emits parameter-only protocol

- **WHEN** a record has platform description `Sentinel-2` and instrument type `MSI`
- **THEN** the Assay MUST have a table `Sensor Acquisition` with parameters `Platform` = `Sentinel-2` and `Instrument` =
  `MSI`, and MUST NOT have invented Input/Output columns on that table

#### Scenario: No acquisition omits the protocol

- **WHEN** a record has empty `acquisition_information`
- **THEN** the Assay MUST NOT have a table named `Sensor Acquisition`
