## ADDED Requirements

### Requirement: IsoParser MUST extract MI_AcquisitionInformation into InspireRecord

When OWSLib exposes `MD_Metadata.acquisition` as `MI_AcquisitionInformation`, the system MUST populate
`InspireRecord.acquisition_information` with each platform that has at least one non-empty identifier or description,
and with each nested instrument that has at least one non-empty identifier or type. Empty names MUST be omitted.
Platforms with neither label nor any kept instrument MUST be omitted. When `acquisition` is missing or yields no kept
platforms, `acquisition_information` MUST be absent or empty per the model default. Existing `inspire-value-bounds` MUST
apply unchanged. Operation/event metadata is not required by this requirement.

#### Scenario: Platform and instrument labels are retained

- **WHEN** `iso.acquisition` has one platform with description `Sentinel-2` and one instrument with type `MSI`
- **THEN** `InspireRecord.acquisition_information` MUST contain that platform and instrument with those values

#### Scenario: Missing acquisition stays empty

- **WHEN** `iso.acquisition` is missing or `None`
- **THEN** `InspireRecord.acquisition_information` MUST be empty / default (no platforms)
