## Why

RDIs write placeholder text instead of leaving fields empty, and the harvester published it as metadata. Live data on
2026-10-05:

- BonaRes (`repository.zalf.de`, 258 valid records): `supplementalInformation` "No information provided" 257, `lineage`
  "None" 105, `otherConstraints` "None" 105, `purpose` "None" 104. Another 44 records failed validation because a
  `graphicOverview` is the string "None" (not an allowed URL scheme).
- Thünen Atlas (151): `supplementalInformation` "No information provided" 9.
- e!DAL (338): 28 `License` Comments "$licenseURL" (unrendered template).

Tracked as GitHub [#413](https://github.com/fairagro/m4.2_middleware_harvester/issues/413).

## What Changes

- New shared helper `middleware.payload.placeholders.is_placeholder`: whole-value, case-insensitive match against a
  value list (default `None`, `null`, `N/A`, `No abstract provided`, `Keine Zusammenfassung vorhanden`,
  `No information provided`), plus unrendered `$var` / `${var}` / `{{var}}` templates.
- INSPIRE: `InspireRecord` and its nested models treat a placeholder in an **optional** field as absent (scalar →
  default, list items removed). The list is configurable as `value_bounds.placeholder_values`.
- Schema.org: the `License`, `Language`, `Version` and `URL` Investigation Comments and the Assay `Comment [License]`
  skip placeholder values. `arc_license` uses the same helper.

Out of scope, decided with the maintainer: required fields keep their value. BonaRes has 194 placeholder abstracts ("No
abstract provided" / "Keine Zusammenfassung vorhanden"); treating them as empty would fail those records. Whether to
publish them without abstract or report them is a follow-up for the API/hub team and BonaRes. Validation models for the
non-INSPIRE parsers (#380) do not exist yet, so the linked-data side uses the default list and is not configurable.

## Capabilities

### Modified Capabilities

- `inspire-to-arc-mapping`: placeholder values in optional record fields.
- `schemaorg-to-arc-mapping`: placeholder licence Comments.

## Impact

- BonaRes: 16 more records validate (274 instead of 258; the other 28 graphic-overview records still fail on an
  over-long `otherConstraints` disclaimer, a separate issue). No optional placeholders remain in BonaRes or Thünen.
- e!DAL: the 28 `$licenseURL` Comments disappear.
