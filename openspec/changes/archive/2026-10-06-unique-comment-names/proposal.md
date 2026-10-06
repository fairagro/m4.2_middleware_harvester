## Why

The API reads every harvested RO-Crate (`ARC.from_rocrate_json_string`) and writes it to the ARC repository with
`ARC.Write`. In Python ARCtrl 3.2.x, `ARC.Write` fails with `TypeError: Object is not iterable` when an Investigation,
Study, Assay or Person has two Comments with the same name. Harvested ARCs often do:

- Publisso: repeated Regal facets (`associatedDataset`, `oth`, …) in 85 of 92 records.
- ARCtrl also duplicates the `dateModified` Comment on read (it keeps the Comment node and adds one from the root
  property), so since `dateModified` was added (#442) all 92 Publisso records had a duplicate.
- BonaRes + Thünen: several organisational creators (`Creator Organization`) in 10 of 425.

With the API's ARCtrl (3.2.2, fable-library 5.18.0), all 92 live Publisso ARCs fail `ARC.Write` after the read.

## What Changes

- New `middleware.payload.arc_comments`, applied once in `HarvestedArc.from_arctrl` (all mappers):
  - `unique_comment_names`: same-name Comments on the Investigation, its Studies, Assays, Persons (Investigation, Study,
    Assay performers) and Publications are merged into the first one, distinct values joined by `; `.
  - `drop_date_modified_comment_node`: the RO-Crate keeps the root `dateModified` but not the `dateModified` Comment
    node, so a read gives exactly one Comment.
- ARCtrl upstream issue drafted for the `ARC.Write` crash and the `dateModified` duplication.

## Capabilities

### Modified Capabilities

- `payload`: harvested ARCs have unique Comment names.

## Impact

- Schema.org `Distribution`, Regal repeated facets and INSPIRE `Creator Organization` with several values become one
  Comment with `; `-joined values instead of several Comments.
- API path (read + `ARC.Write`, arctrl 3.2.2 / fable-library 5.18.0) on live data: Publisso 0/92 failures (was 92/92),
  BonaRes + Thünen 0/425, e!DAL 0/338.
