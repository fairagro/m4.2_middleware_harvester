## Why

Unchanged OpenAgrar / Schema.org datasets produce a new Middleware `arc_hash` (and thus Git commits) on every harvest because `GeneralSchemaOrgMapper` is non-deterministic for keywords, multi-literal description selection, and creator/author/contributor iteration order. API-side hash canonicalization does not cover these content/@id churns.

## What Changes

- Collect and sort keyword literals before joining Investigation / protocol Keyword strings.
- Replace non-deterministic `graph.value` / `_str` selection with a stable multi-literal policy (prefer `en`, then `de`, then untagged; drop empty; tie-break by length then lexicographic order).
- Sort creator / author / contributor nodes by a stable key before appending Contacts so Publication author strings and derived `#Author_*` nodes stop oscillating.
- Optionally format Publication authors without `Last, F.` comma form so ARCtrl does not split names on commas.
- Add unit tests proving same logical payload → identical relevant Investigation state across RDF object orders and double maps.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `linked-data-mapper`: Schema.org mapping MUST be harvest-deterministic for keywords, multi-literal string fields (at least description), and contact/publication-author order.

## Impact

- Code: `middleware/linked_data/.../general_schema_org_mapper.py`
- Tests: `middleware/linked_data/tests/unit/test_mapper.py`
- Specs: `openspec/specs/linked-data-mapper/`
- Non-goals: Middleware API hash logic; Regal mapper; other RDI-specific mappers beyond the shared Schema.org mapper.
