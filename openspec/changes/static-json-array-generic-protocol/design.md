# Design

## Key Decisions

### 1. Static JSON array discovery is a generic Protocol

The source is one non-paginated JSON document, so discovery is a small `Protocol` subclass
(`middleware/generic/protocol/static_json_array.py`), **because** `linked_data` is being phased out and the record
payload is handled by the shared `jsonld` parser, so no dataset class is needed.

### 2. Content-hash composite identifier

`genomes.json` has about 80 DOIs shared by 2–3 records each (one paper describing several species' genomes). The
discovery identifier is `sanitize_identifier(@id | identifier) + ":" + sha256(canonical JSON)[:16]`. This keeps distinct
records apart and gives the same identifier when the array is re-ordered. Byte-identical records collapse through
`Protocol.discover()` deduplication. The identifier is passed as `harvest_source_id` so `schema_org_general` produces a
distinct `Investigation.identifier` per record instead of falling back to the shared DOI subject IRI.

### 3. Schema.org context IRIs are resolved locally by the jsonld parser

Every PlabiPD record uses `"@context": "http://schema.org"`. Fetching it would mean one uncached, impolite network
request per record (rdflib caches contexts per parse only; about 0.6 s each), outside `NiceHttpClient`. The parser
replaces exact top-level Schema.org IRIs with `{"@vocab": "http://schema.org/"}`. For `genomes.json` this gives the same
triples as the remote context. Any other remote context string is still rejected, so parsing never goes to the network.
