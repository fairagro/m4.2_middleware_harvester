# Proposal

## Why

Keyword-producing mappers disagree on ARC shape. Regal already writes per-term Investigation Comments
(`keyword [<URI>]`, `keyword [DDC:<URI>]`) plus a transitional aggregate `Keywords`. Schema.org, ckanext-dcat, and
INSPIRE mostly emit only the aggregate (or equivalent). MODS and Phenoroam put comma-joined labels only on a Study
`Data Collection` protocol Parameter — which is not the API / Search Hub keyword path.

Issue #603 locks a **uniform Investigation Comment contract** (keep aggregate until #604 / api#663). ArcInvestigation
has no first-class keywords field; Comments are the agreed surface the API already exports / will materialize as
DefinedTerms. OntologyAnnotation keyword lists on the Investigation are out of scope here (#417 AC superseded).

## What Changes

- Introduce a shared keyword-comment helper and OpenSpec contract: every subject/plain term → unique
  `keyword [<URI|label>]` Comment; optional DDC → `keyword [DDC:<URI>]` only when a class URI is known; aggregate
  `Keywords` = comma-joined **subject/plain labels only** (trim / casefold-dedupe / sort; no DDC labels).
- Align **all** keyword-producing mappers: inspire_general, schema_org_general, regal_general, ckanext_dcat,
  mods_general, phenoroam_general.
- Regal: replace bare `keyword` (no URI) with `keyword [<label>]` for unique names.
- MODS / Phenoroam: **remove** Study table Parameter `Keywords`; emit Investigation Comments instead.
- ckanext-dcat: keep Investigation Comments as SoT; drop duplicate Keywords **protocol parameter** when present so
  behaviour matches other mappers (Processing Description / Language unchanged).
- Document the contract in `docs/mappers/*` (Regal as reference) and clarify #417 relation (Comments first).

## Capabilities

### New Capabilities

- `keyword-comments`: Shared Investigation Comment naming / aggregate / uniqueness contract for keyword terms across
  mappers.

### Modified Capabilities

- `inspire-to-arc-mapping`: emit per-term Comments from `KeywordTerm` (name + optional url); keep aggregate;
  URI/thesaurus emission rules for Comments (thesaurus title not required in Comment name for this issue).
- `schemaorg-to-arc-mapping` / `linked-data-mapper`: per-term Comments alongside existing aggregate determinism.
- `regal-to-arc-mapping`: align plain-term names to `keyword [<label>]`; keep DDC + aggregate rules.
- `ckanext-dcat-to-arc-mapping`: per-term Comments; remove Keywords from Dataset Processing parameters.
- `mods-to-arc-mapping`: Investigation Comments; remove Study Data Collection Keywords parameter.
- `phenoroam-to-arc-mapping`: Investigation Comments; remove Study Data Collection Keywords parameter.

## Impact

- `middleware/payload` shared helper + mapper call sites; unit tests per mapper (URI+label, plain-only, DDC
  present/absent).
- Mapper docs under `docs/mappers/`.
- No API package change; aggregate remains until #604.
- Follow-ups: #604 remove aggregate; api#663 materialization; #417 stays Comments-contract-first.
