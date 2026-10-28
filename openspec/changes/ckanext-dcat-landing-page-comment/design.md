# Design

## Context

See proposal.md. The `ckanext_dcat` mapper already derives the Investigation identifier and the Assay `Output [URI]`
fallback from the dataset IRI, and reads values through the stable graph view so value order is deterministic.

## Goals / Non-Goals

**Goals:** one `Landing Page` comment per DCAT-AP Investigation, generic for any ckanext-dcat catalogue.

**Non-Goals:** resolving URLs over HTTP; per-RDI URL templates in config.

## Decisions

- **`dcat:landingPage` first, then the dataset IRI.** DCAT-AP defines `dcat:landingPage` as the landing page, so an
  explicit value wins. The IRI fallback is used because ckanext-dcat mints dataset IRIs as `{ckan}/dataset/{id}`, the
  CKAN dataset page, so it is generic for this mapper. Alternative: a configured URL template per repository; rejected
  because the IRI already carries the page and config would duplicate it.
- **Only http(s) values.** A non-http(s) IRI (e.g. `urn:`) or blank node is not a page; writing it would give the Search
  Hub a dead link.
- **No `URL` comment.** `Landing Page` is the key the API export (#617) reads; `URL` exists only for schema.org
  compatibility and is due for removal.

## Risks / Trade-offs

- [A ckanext-dcat site configured with a custom URI base whose IRIs are not pages] → the comment would point at a
  non-page; such a catalogue can export `dcat:landingPage`, which wins. Checked for SRADI on the dev stack.
