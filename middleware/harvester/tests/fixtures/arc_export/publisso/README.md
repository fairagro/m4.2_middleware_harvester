# PUBLISSO / Regal (publisso) arc-export fixtures

Root `ro-crate-metadata.json` is the MVP smoke crate. Nested dirs are real-data cases (#611).

## Real-data cases

Generated from live Regal `/find` (`https://frl.publisso.de/find`, `q=contentType:researchData`) through `JsonLdParser`
(`allowed_context_url: https://frl.publisso.de/context.json`) + `RegalMapper`
(`resource_base_url: https://repository.publisso.de/resource/`), matching `dev_environment/config.all-rdis.yaml`. Person
`email` values redacted to `redacted@example.invalid` when present (none in this curated set).

- `frl_6420709/`: `@id` `frl:6420709`; features: multi person (given-name), mixed ORCID / adhoc agent ids, institution
  comment, subjects + DDC keyword comments, ODC-By license, landing page, DOI, recording period (temporal extent)
- `frl_6407998/`: `@id` `frl:6407998`; features: multi person + ORCID, subjects + DDC keyword comments, CC-BY license,
  landing page, DOI, spatial sampling (location + coordinates), recording period; source also carries `joinedFunding` /
  funder edges (list-shaped `joinedFunding` may not emit Data Processing Funder parameters today)
- `frl_6472531/`: `@id` `frl:6472531`; features: large person contact set without ORCID (adhoc agent ids + given-name),
  organization affiliation, subjects + DDC keyword comments, CC-BY license, landing page, DOI
