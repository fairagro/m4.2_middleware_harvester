## Why

GeoNode CSW catalogues (BonaRes, Thünen Atlas) write the dataset DOI as `doi:https://doi.org/10.4228/…` with the link
`https://dx.doi.org/https://doi.org/…`. `InspireMapper` passed `resource_identifier.code` unchanged into
`Publication.doi`; ARCtrl writes it as the citation `identifier` `@id`, and JSON-LD expansion downstream turns the
`doi:` CURIE into `https://dx.doi.org/<rest>`. In the DataHUB export 1,526 BonaRes citation identifiers start with
`https://dx.doi.org/`, 1,344 of them doubled. Any code containing `doi` (also accession URLs) or with an ISBN codespace
became a Publication `doi`. Tracked as GitHub [#410](https://github.com/fairagro/m4.2_middleware_harvester/issues/410).

## What Changes

- New shared helper `middleware.payload.dois.normalize_doi`: strips `doi:`, `doi.org`, `dx.doi.org` and `www.doi.org`
  prefixes repeatedly and returns the bare `10.<registrant>/<suffix>` DOI, else `None`. `stable_graph.normalize_doi`
  (Schema.org) is replaced by it; the Regal `doi` field goes through it too.
- INSPIRE mapper: one Publication per distinct DOI (from the identifier code, else its URL), in bare form. Codes that
  are not DOIs (ISBN, accession URLs, UUIDs) no longer become Publications.

Out of scope: whether the dataset's own DOI should be an ARC Publication at all (all mappers do this today); that needs
the API team and stays open on #410.

## Capabilities

### Modified Capabilities

- `inspire-to-arc-mapping`: DOI normalisation.

## Impact

- BonaRes and Thünen ARCs change once after deploy (bare DOI in the citation `identifier`). Live Thünen + BonaRes
  repository-e (165 records): 21 DOI codes, all bare after mapping. Regal (Publisso) DOIs are already bare and
  unchanged.
