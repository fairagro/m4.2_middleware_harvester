## Why

OpenAgrar asked us to stop scraping its rendered record pages (`/receive/{id}`) and to use its REST API instead
(fairagro/m4.2_basic_middleware#257). Page rendering is expensive on their side. A parallel basic-middleware run took
the site down on 2026-10-20, and the shared egress IP was then dropped from the OpenAgrar WAF allow list. Record-page
requests now face the proof-of-work gate again (#271). The MyCoRe REST API (`/api/v2/objects`) serves the same 933
published research-data records as structured MODS XML, which is cheaper for them and richer for us (DOI, licence,
ORCID/GND, affiliations). Tracked in #503.

## What Changes

- New generic **Protocol `mycore_rest`**. It discovers objects from a MyCoRe REST v2 object list (`entry_url` carries
  the operator's category filters), pages with `after_id`, and reports the expected count from `X-Total-Count`. It
  yields one discovery unit per object. The landing page (`/receive/{id}`) is the unit's identity and source URL, and
  the REST object URL is what gets fetched. The protocol is reusable for any MyCoRe repository; no OpenAgrar values are
  in code.
- New optional **fetch URL on URL discovery units**. A Protocol can name a machine-readable payload URL that differs
  from the human landing page. Parsers that fetch use it when it is set.
- New shared **PayloadParser `mods_xml`** producing a new **`PayloadKind.mods_record`**. It fetches the MyCoRe object
  XML (or accepts a bare `mods:mods` document), extracts the `mods:mods` element with the shared safe XML parsing, and
  returns a typed MODS intermediate record.
- New shared **DataMapper `mods_general`**. It maps `mods_record` directly to ARC: title, abstract, creators with
  ORCID/GND and affiliation, DOI, licence, issue date and subjects. It does not convert through Schema.org/RDF. The
  authoritative field rules go in a new `docs/mappers/mods.md`.
- ARC identity is unchanged for existing OpenAgrar ARCs. Investigation.identifier stays the MyCoRe object id, as
  `mycore_solr` + `schema_org_general` produce today, so the API updates existing ARCs instead of creating duplicates.
- Not breaking. `mycore_solr`, `html_jsonld` and `schema_org_general` stay as they are. Switching the OpenAgrar
  deployment config (m4.2_infrastructure) is an operator step after release.

### Non-goals

- Incremental harvesting with `modified_after`. It needs persisted harvest state, so it is a follow-up issue.
- Removing or deprecating `mycore_solr` discovery or the OpenAgrar `html_jsonld` path. That waits until the new path has
  run on fizz and draven.
- File/derivate harvesting (`/api/v2/objects/{id}/derivates`). The ARC stays metadata-only.
- An OAI-PMH `mods` metadataPrefix. It would reuse `mods_xml` + `mods_general`, but nothing is configured or tested for
  it here.
- RDI-specific MODS overlays. If one is needed, it becomes a `docs/mappers/rdi/` delta later.

## Capabilities

### New Capabilities

- `mycore-rest-protocol`: the generic `mycore_rest` Protocol. Object-list discovery, `after_id` paging, expected count,
  landing URL versus fetch URL, and error handling.
- `mods-xml-parser`: the shared `mods_xml` PayloadParser. MyCoRe envelope and bare-MODS input, safe XML parsing,
  fail-closed rules, and the `mods_record` output.
- `mods-to-arc-mapping`: the `mods_general` DataMapper implementation contract. Identity cascade, person contacts
  policy, licence/DOI placement, and refusal rules. Field tables live in `docs/mappers/mods.md`.

### Modified Capabilities

- `harvest-protocol`: URL discovery units MAY carry a fetch URL distinct from the landing URL. `mycore_rest` becomes a
  registered type key.
- `payload-parser`: register the `mods_xml` parser type. URL-fetching parsers fetch the discovery unit's fetch URL when
  set.
- `payload`: add `PayloadKind.mods_record` and the `mods_general` mapper registration.
- `mapper-docs`: add MODS to the set of productive base mapper documents.

## Impact

- Code: `middleware/generic` (new protocol module, `ProtocolType`), `middleware/parsing` (discovery type field, new
  parser, `ParserType`, fetch-URL use in `html_jsonld`), `middleware/payload` (new `mods` package with models and
  mapper, `PayloadKind`, `MapperType`, registration).
- Docs: `docs/mappers/mods.md`, `docs/mappers/README.md`, AGENTS.md spec index.
- Config: new keys `generic.protocol.mycore_rest`, `parser.mods_xml`, `mapper.mods_general`. No existing key changes.
- Dependencies: none new (`defusedxml` is already used by `middleware.parsing`).
- Deployment: m4.2_infrastructure fizz values change the OpenAgrar entry after release (Carsten rolls out). Requests go
  only to `/api/v2/`. With `worker_tasks: 1` and the default host rate limit, the run is sequential: 1 list request plus
  ~933 object requests.
- Related: #271, #464, #164, fairagro/m4.2_basic_middleware#257, fairagro/m4_rdi_portfolio#10 and #18.
