# Design

## Key Decisions

### 1. DCAT-AP lives in `generic`, not `linked_data` or a new top-level plugin

The harvester is implemented in-house (rdflib + Hydra pagination) rather than via a third-party DCAT-AP library, so it
fits the `generic` Protocol → PayloadParser → DataMapper framework, **because** `linked_data` is being phased out and a
top-level plugin is only warranted when a third-party client dictates its own loop.

### 2. The Protocol splits pages into per-record inline JSON-LD

A ckanext-dcat page is one flattened JSON-LD document describing many datasets. The Protocol parses a page once,
extracts each dataset's CBD plus one hop (`dcat:distribution`, `dcterms:publisher`, `dcat:contactPoint`,
`dcterms:spatial`), and serializes it as expanded JSON-LD (`{"@graph": [...]}`, no `@context`) in a
`JsonLdDiscoveryResult`, **because** one discovery unit must be one record, and a shared JSON-LD parser keeps the
Protocol content-agnostic and reusable. The extra serialize/parse per record is small compared with the HTTP cost.

### 3. The JSON-LD parser has no `@context` allowlist but refuses remote contexts

Unlike HTML Schema.org scraping, inline JSON-LD may use any vocabulary (DCAT-AP, Regal, …), so a Schema.org allowlist
does not apply; remote `@context` / `@import` strings are rejected, **because** parsing must never trigger network
retrieval from attacker-controlled payloads.

### 4. The mapper key is `ckanext_dcat`

The mapper unwraps CKAN-specific JSON-string fields emitted by `ckanext-dcat`, **because** that flavour, not DCAT-AP in
general, is what it handles; a plain-DCAT-AP mapper can be added under a separate key later.
