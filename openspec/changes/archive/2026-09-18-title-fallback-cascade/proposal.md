## Why

Issue #164: some OpenAgrar (and other `schema_org_general`) records have no
`schema:name`, so `GeneralSchemaOrgMapper` rejected them outright even though
a usable title exists elsewhere on the same record (`schema:headline`,
`schema:alternativeHeadline`, or the fetched HTML page's own `<title>` /
`citation_title` meta tag). The spec's "Fail closed on missing required
fields" requirement said `schema:name` itself was required with no
fallbacks; PR #221 implements a fallback cascade instead, which needs to be
reflected here before that requirement text is stale relative to the code.

## What Changes

- Add a new "Title fallback cascade when schema:name is missing" requirement:
  `schema:name` → `schema:headline` → first non-empty
  `schema:alternativeHeadline` **in document order** → (`html_jsonld` sources
  only) HTML `citation_title` / `<title>` hint. A fallback (anything but
  `schema:name` itself) MUST be recorded as a `"Title Source"` Investigation
  Comment and logged at WARNING, and MUST NOT ever surface an rdflib
  blank-node label.
- Narrow "Fail closed on missing required fields" so the `schema:name` bullet
  now reads "no usable title after the full title-fallback cascade", with a
  scenario reflecting that.

## Non-Goals

- Changing the harvester-report `WARNING` issue kind (out of reach without a
  `fairagro-middleware-shared` release; PR #221 uses `logger.warning` + a
  Comment instead — see that PR's description).
- Regal / INSPIRE title resolution (unaffected).
- Any change to `Investigation.identifier` resolution (separate cascade,
  already specified).

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`: title resolution is now a fallback cascade
  instead of a single required field.

## Impact

- **Affected domains**: `openspec/specs/schemaorg-to-arc-mapping/`.
- **Code**: [`general_schema_org_mapper.py`](../../../middleware/linked_data/src/middleware/linked_data/linked_data_mapper/general_schema_org_mapper.py),
  [`linked_data_mapper.py`](../../../middleware/linked_data/src/middleware/linked_data/linked_data_mapper/linked_data_mapper.py)
  (`MappingContext.html_title`), [`html_jsonld.py`](../../../middleware/linked_data/src/middleware/linked_data/dataset/html_jsonld.py)
  (`title_hint` / `title_hint_from_cache`), [`plugin.py`](../../../middleware/linked_data/src/middleware/linked_data/plugin.py);
  tests under [`middleware/linked_data/tests/`](../../../middleware/linked_data/tests/).
- **API / config / dependencies**: none. Already implemented and tested on
  PR #221 (`feature/openagrar-title-fallback-164`); this proposal documents
  that landed behavior in the spec.
