## ADDED Requirements

### Requirement: IsoParser MUST extract keyword names from OWSLib MD_Keywords

When parsing ISO 19139 identification metadata into `InspireRecord`, the system MUST populate `InspireRecord.keywords`
with the non-empty keyword **names** from each OWSLib `MD_Keywords` entry on `identification.keywords`. Plain `str` list
items MUST still be accepted. Empty names MUST be omitted. Existing `inspire-value-bounds` list and string limits on
`keywords` MUST continue to apply unchanged (fail the record on violation; do not silently truncate). Thesaurus title,
keyword type, and `gmx:Anchor` URI MUST NOT be required for this requirement (deferred).

#### Scenario: MD_Keywords objects yield keyword names

- **WHEN** `identification.keywords` is a list of OWSLib `MD_Keywords` whose nested `keywords` entries have names
  `crop rotation` and `Germany`
- **THEN** `InspireRecord.keywords` MUST contain those names (order of groups MAY be preserved as listed; empty names
  omitted)

#### Scenario: Plain string keywords still work

- **WHEN** `identification.keywords` is a list of strings `["a", "b"]`
- **THEN** `InspireRecord.keywords` MUST be `["a", "b"]`

#### Scenario: Empty keyword list stays empty

- **WHEN** `identification.keywords` is missing or empty
- **THEN** `InspireRecord.keywords` MUST be an empty list
