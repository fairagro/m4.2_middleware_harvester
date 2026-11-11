# e!DAL (edal) arc-export fixtures

No smoke crate at this folder root — real-data cases only (#610).

## Real-data cases

Generated via live e!DAL HTML/JSON-LD (`https://doi.org/10.5447/ipk/…` → `doi.ipk-gatersleben.de`) through
`HtmlJsonLdParser` (`allowed_context_url: http://schema.org`) + `GeneralSchemaOrgMapper` with
`placeholders.unrendered_templates: true` (drops `$licenseURL`, #413). Person `email` values redacted to
`redacted@example.invalid` when present.

- `10_5447_ipk_2011_0/`: DOI `10.5447/ipk/2011/0`; features: person (multi), ORCID, flat address / affiliation,
  keywords, license, landing page, publisher, organization comments
- `10_5447_ipk_2016_12/`: DOI `10.5447/ipk/2016/12`; features: Creator Organization (no Person nodes), keywords,
  license, landing page, publisher
- `10_5447_ipk_2012_1/`: DOI `10.5447/ipk/2012/1`; features: person, address / affiliation, keywords, license, landing
  page, publisher
