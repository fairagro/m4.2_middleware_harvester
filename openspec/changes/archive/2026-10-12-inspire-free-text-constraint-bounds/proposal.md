# Proposal

## Why

#433: 664 of 978 records in the live BonaRes catalogue (`repository.zalf.de`, 2026-10-05) fail validation with
`other_constraints.N: string of length 1136 exceeds value_bounds.max_str_medium=1000`. `InspireRecord.other_constraints`
uses the single-line limit, but `gmd:otherConstraints` is free text. BonaRes puts a full author disclaimer there. Since
a violating value fails the whole record, two thirds of the catalogue never reaches the hub.

## What Changes

- The two free-text constraint lists use the paragraph limit (`max_str_long`) per element:
  - `other_constraints` (`gmd:otherConstraints`)
  - `constraints` (`gmd:useLimitation`), which holds the same kind of text
- The codelist constraint lists (`access_constraints`, `use_constraints`, `classification`) keep `max_str_medium`. Their
  values are `MD_RestrictionCode` / `MD_ClassificationCode` entries, so a long value there is still an error.
- `ValueBounds.max_str_long` description names free-text constraints.
- **Non-goals:** changing the default limits; truncating values; the other BonaRes failures from the same run (missing
  abstract, `Creation` date type).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-value-bounds`: free-text constraint elements are bounded by `max_str_long`.

## Impact

- `middleware/payload/src/middleware/payload/inspire/models.py`, `value_bounds.py`
- `middleware/inspire/tests/unit/test_iso_parser.py`
