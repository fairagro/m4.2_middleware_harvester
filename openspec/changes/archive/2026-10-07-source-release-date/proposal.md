## Why

The mappers wrote the source publication date to `SubmissionDate`, which ARCtrl ≥ 3.2 exports as RO-Crate `dateCreated`,
and left `PublicReleaseDate` empty, which ARCtrl fills with the serialisation time as `datePublished`. In the DataHUB
export every first-phase record therefore showed its publication date as the creation date, and a `datePublished` that
changed on every harvest run. Tracked as GitHub
[#407](https://github.com/fairagro/m4.2_middleware_harvester/issues/407).

With arctrl 3.2.2 (the API's version), `PublicReleaseDate` and `SubmissionDate` survive the API's
`ARC.from_rocrate_json_string` → `ARC.Write` → load round trip unchanged, so this is a harvester-only change.

## What Changes

- The source publication date goes to Investigation and Study `PublicReleaseDate` (RO-Crate `datePublished`); the source
  creation date, when there is one, to `SubmissionDate` (RO-Crate `dateCreated`).
- `PublicReleaseDate` falls back to the other source dates, so the harvest time is only used when the source has no date
  at all (decided with the maintainer). `SubmissionDate` is never filled from another date.
- Schema.org: `datePublished`, else `dateModified`, else `dateCreated`; `dateCreated` → `SubmissionDate`.
- INSPIRE: earliest `publication`, else latest `revision`, else earliest `creation` citation date; earliest `creation` →
  `SubmissionDate`.
- Regal: `dcterms:issued` (it has no creation date).
- ckanext-dcat: `dcterms:issued`, else `dcterms:modified`.

Out of scope: `sdDatePublished` (the API's serialisation time, fairagro/m4.2_advanced_middleware_api#365) and PhenoRoam,
whose `md_change_date` is a metadata date.

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`, `inspire-to-arc-mapping`, `regal-to-arc-mapping`, `ckanext-dcat-to-arc-mapping`: source
  publication and creation dates.

## Impact

- RO-Crate `datePublished` holds the source date and stays stable across harvest runs; `dateCreated` appears only for
  sources with a creation date.
