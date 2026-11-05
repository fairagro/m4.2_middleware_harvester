# Design

## Context

See proposal.md — Why. Soft-deprecation (#461) left `CkanextDcatMapperConfig.catalog_name` / `catalog_url`, a
deprecation warning validator, flat `MapperConfig.catalog_*` accessors, and `CkanextDcatMapper` writing
`Comment("Data Catalog")`. Catalog/RDI provenance is owned by the API `known_rdis` path. Infra overlays no longer set
the keys.

## Goals / Non-Goals

**Goals**

- Delete the deprecated config fields and warning path
- Stop emitting `Investigation.Comment("Data Catalog")` from the DCAT mapper
- Align OpenSpec + mapping doc + tests with hard removal

**Non-Goals**

- Changing API `known_rdis` behaviour or Investigation RDI comments (API-owned)
- Renaming or restructuring other mapper type configs
- Soft-warn or migration-only error string for leftover `catalog_*` (forbid-extra on the type child already rejects
  unknown keys)

## Decisions

1. **Hard delete fields on `CkanextDcatMapperConfig`** — Remove fields, blank validators, and
   `_warn_deprecated_catalog_fields`. Drop `ckanext_dcat` from `_MAPPER_TYPE_LOCAL_FIELDS` (or empty set). Remove
   `MapperConfig.catalog_name` / `catalog_url` properties and `_LEGACY_CATALOG_FIELDS_MSG`.
2. **Mapper constructor** — Drop `catalog_name` / `catalog_url` from `CkanextDcatMapper` / `_CkanextDcatRun`; delete the
   Data Catalog comment branch.
3. **Docs** — Rewrite `docs/mappers/ckanext-dcat.md` so catalog provenance is API-only (no deprecated config rows /
   fallbacks).
4. **Spec** — MODIFY `Register a ckanext_dcat DataMapper` and `Map dcat:Dataset to ARC Investigation, Study and Assay`
   to remove catalog config and comment obligations.

## Risks / Trade-offs

- [Out-of-repo YAML still setting `catalog_*`] → Expected BREAKING; type-child `extra="forbid"` fails at startup.
  Operators must rely on API `known_rdis`.

## Migration Plan

1. Confirm deployment configs omit `mapper.catalog_*` / `mapper.ckanext_dcat.catalog_*` (done for fizz/draven).
2. Upgrade harvester; leftover keys fail validation.
3. Verify SRADI Investigation catalog/RDI comments still appear from the API registry.
