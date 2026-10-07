## Why

No e!DAL ARC carried its dataset DOI (0 of 338 live), although every e!DAL dataset is a DOI. e!DAL writes the Dataset
`@id` as a bare DOI (`"@id": "10.5447/ipk/2011/0"`) and no `schema:identifier`. JSON-LD reads a bare DOI as a relative
IRI, and rdflib resolved it against the harvester's working directory (`file:///app/10.5447/ipk/2011/0`), so the
mapper's DOI lookup on the subject IRI never matched. Part of GitHub
[#416](https://github.com/fairagro/m4.2_middleware_harvester/issues/416) (typed, resolvable dataset identifiers); the
identifier representation in the basic layout is still to be agreed with the API and Search Hub teams.

## What Changes

- New `middleware.parsing.jsonld_doi_ids.doi_ids_as_iris`: every JSON-LD `@id` that is a bare DOI becomes
  `https://doi.org/<doi>` before rdflib parses the block. Used by the `html_jsonld` and `jsonld` parsers.
- The schema.org mapper then finds the DOI on the subject IRI as before and writes it as a Publication DOI, which ARCtrl
  exports as a `PropertyValue` named `DOI` (propertyID `OBI_0002110`).
- The ARC identifier is unchanged (it comes from the discovered page URL).

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`: the dataset DOI from a bare-DOI `@id`.

## Impact

- Live e!DAL: typed DOI on 338 of 338 ARCs (was 0); identifiers unchanged.
- Other `html_jsonld` / `jsonld` sources only change where an `@id` is a bare DOI.
