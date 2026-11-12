# PlabiPD (plabipd) arc-export fixtures

No smoke crate at this folder root — real-data cases only (#613).

## Real-data cases

Generated from live pubplant dump
(`https://raw.githubusercontent.com/usadellab/pubplant2schemaorg/gh-pages/genomes.json`) through
`PubplantJsonArrayProtocol` composite identity (`{sanitized_doi}:{sha256[:16]}`) + `JsonLdParser`
(`allowed_context_url: http://schema.org`) + `GeneralSchemaOrgMapper`, matching `dev_environment/config.all-rdis.yaml`.
Person `email` values redacted to `redacted@example.invalid` when present (none in this curated set). Case directories
use `_` instead of `:` in the composite id.

- `doi_org_10_1038_35048692_7cc2766e3ba04cda/`: DOI `10.1038/35048692`; features: Creator Organization (no Person
  contacts), keywords, CC-BY license, publisher, composite discovery id
- `doi_org_10_1126_science_1068037_ba8b7534c1f9b69a/`: DOI `10.1126/science.1068037`; features: multi Person
  (givenName/familyName), keywords, CC-BY license, publisher, composite discovery id
- `doi_org_10_1038_ng_2684_22c554249fb7f833/` and `doi_org_10_1038_ng_2684_3d96e30783406059/`: shared DOI
  `10.1038/ng.2684` with distinct content hashes (pubplant collision pair — Gladecress vs London rocket keywords);
  features: multi Person (givenName/familyName), keywords, CC-BY license, publisher, composite discovery ids
