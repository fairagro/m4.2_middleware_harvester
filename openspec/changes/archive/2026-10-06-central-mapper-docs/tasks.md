# Tasks

## 1. Layout scaffold

- [x] 1.1 Create `docs/mappers/` and `docs/mappers/rdi/`; add thin `docs/mappers/README.md` with layout, front-matter
      schema (`payload_kind`, optional `mapper_id`, overlay `builds_on`), required section headings, and a short note
      that Markdown is the intended future code-generation input (generator not implemented) — verify README renders and
      links resolve locally
- [x] 1.2 Update `openspec/principles.md` Foundation Contract (and any other live principles pointers) so mapping docs
      are described under `docs/mappers/` — verify `rg 'docs/mappers' openspec/principles.md` hits and old flat paths
      are gone from that narrative

## 2. Relocate existing base docs

- [x] 2.1 `git mv` `docs/schemaorg_mapping.md` → `docs/mappers/schemaorg.md`, `docs/regal_mapping.md` →
      `docs/mappers/regal.md`, `docs/inspire_mapping.md` → `docs/mappers/inspire.md`; add MVP front matter — verify old
      paths absent (`test ! -e docs/schemaorg_mapping.md` etc.)
- [x] 2.2 Update live references (OpenSpec `openspec/specs/**`, product READMEs, `docs/**`, code comments under
      `middleware/`) from the old filenames to the new paths — verify
      `rg 'docs/(schemaorg|regal|inspire)_mapping\\.md' --glob '!openspec/changes/archive/**'` returns no hits

## 3. Author missing base mapping docs from code

- [x] 3.1 Write `docs/mappers/phenoroam.md` from `middleware/payload/.../phenoroam/mapper.py`, unit tests, and
      `openspec/specs/phenoroam-to-arc-mapping/` using the same section shape as other base docs — verify the doc covers
      every mapped field/comment path exercised in `test_phenoroam_mapper.py`
- [x] 3.2 Write `docs/mappers/ckanext-dcat.md` from `.../ckanext_dcat_mapper.py`, unit tests, and
      `openspec/specs/ckanext-dcat-to-arc-mapping/` — verify the doc covers catalog config, distribution table, and CKAN
      JSON org unwrapping covered in `test_ckanext_dcat_mapper.py`

## 4. Audit existing docs vs spec vs code

- [x] 4.1 Three-way audit Schema.org: `docs/mappers/schemaorg.md` ↔ `schemaorg-to-arc-mapping` ↔
      `general_schema_org_mapper.py` (+ related helpers/tests); record mismatches; fix docs/specs in this change when
      they lag intentional behaviour — verify a short audit note in the PR/change (or task comment) lists findings and
      resolutions
- [x] 4.2 Same audit for Regal (`regal.md` ↔ `regal-to-arc-mapping` ↔ `regal_mapper.py`) — verify same as 4.1
- [x] 4.3 Same audit for INSPIRE (`inspire.md` ↔ `inspire-to-arc-mapping` ↔ `inspire/mapper.py`) — verify same as 4.1
- [x] 4.4 If an audit finding requires a behavioural code change, open a linked GitHub issue via `/create-issue`
      (`relation: linked` to #170) and do **not** silently change mapper behaviour here — verify issue URL recorded in
      the PR body when applicable

## 5. RDI overlays (only if real deltas)

- [x] 5.1 Scan shipped helm/dev configs and mapper code/tests for RDI-specific deltas vs a base mapper; if any are
      concrete, add `docs/mappers/rdi/<rdi>_<base>.md` with `builds_on` and delta-only content; otherwise leave `rdi/`
      empty aside from README guidance — verify either overlay files validate the README naming rule or explicitly no
      overlays were warranted

## 6. OpenSpec domain Purpose / delta alignment

- [x] 6.1 Update Purpose / authoritative-source links on live specs (`schemaorg-to-arc-mapping`, `regal-to-arc-mapping`,
      `inspire-to-arc-mapping`, `phenoroam-to-arc-mapping`, `ckanext-dcat-to-arc-mapping`) to `docs/mappers/…` — verify
      each Purpose (or ADDED requirement) points at the new path
- [x] 6.2 Run `openspec validate --change central-mapper-docs` (or project equivalent) and fix any delta issues — verify
      validation succeeds

## 7. Integration check

- [x] 7.1 Spot-check that README.md / middleware package READMEs that cited old mapping paths still navigate correctly —
      verify manual link check for the three relocated docs plus the two new ones
