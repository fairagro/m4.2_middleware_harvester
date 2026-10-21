## Context

See proposal.md (Why). OpenAgrar is harvested today through `generic` with `mycore_solr` discovery
(`/servlets/solr/select`), `html_jsonld` parsing of `/receive/{id}`, and `schema_org_general` mapping. ARC identity is
the MyCoRe object id, passed as `harvest_source_id`. The generic pipeline already gives per-record concurrency
(`worker_tasks`) and host rate limiting (`NiceHttpClient.max_requests_per_second`), so making the run sequential is a
config question, not a code question. `middleware.parsing` parses inline XML with `defusedxml` (`phenoroam_xml`). The
hardened lxml default parser (csw-xml-hardening) is scoped to the INSPIRE/OWSLib path.

Verified against the live API on 2026-10-20/21:

- `GET /api/v2/objects?category=…` returns `<mycoreobjects><mycoreobject id lastModified/>` and `X-Total-Count`, with
  `limit` and `after_id` paging.
- `GET /api/v2/objects/{id}` returns `mycoreobject` XML with `mods:mods` under
  `metadata/def.modsContainer/modsContainer`.
- OpenAgrar's robots.txt disallows `/api/` (only `/api/v1/objects/` is allowed) and `/*?`.

## Goals / Non-Goals

**Goals:**

- Requests to OpenAgrar go only to `/api/v2/`.
- Every piece (protocol, parser, mapper) works for any MyCoRe/MODS source.
- Existing OpenAgrar ARCs are updated in place, not duplicated.

**Non-Goals:** as listed in proposal.md. This design also does not change the generic pipeline, the orchestrator, or the
NiceHttpClient.

## Decisions

### D1. Three registry pieces under `generic`, not a new plugin

`mycore_rest` (Protocol) + `mods_xml` (PayloadParser) + `mods_general` (DataMapper) are selected per repository like
SRADI and PlabiPD. Reason: the plugin contract (principles.md) already separates discovery, parsing and mapping. A
dedicated `mycore` plugin would duplicate the pipeline, reporting and concurrency code for no new behaviour. Alternative
considered: extending `mycore_solr` with a REST mode. Rejected because the two endpoints share neither query syntax,
paging nor response format.

### D2. Landing URL is identity; the REST URL is a separate `fetch_url`

`UrlDiscoveryResult` gains optional `fetch_url`. `mycore_rest` sets `identifier = {base}/receive/{id}`,
`harvest_source_id = id`, `fetch_url = …/api/v2/objects/{id}`. Fetching parsers use `fetch_url or url`. Reason: the
source URL sent to the API and the dedup key must stay the human landing page, the same as today's `mycore_solr` units.
That way Search Hub links, harvest reports and existing ARCs do not change. Only the transport moves. Alternatives
considered:

- Use the REST URL as identifier. Rejected because the source URL would change to an API URL, and every ARC would report
  a new source.
- Let the Protocol fetch each object and yield `XmlDiscoveryResult`. Rejected because it serialises fetching inside
  discovery, bypasses the worker pool and its error wrapping, and loses the landing URL (`XmlDiscoveryResult` has no
  source URL).
- Have the parser derive the REST URL from `/receive/{id}`. Rejected because that puts MyCoRe URL knowledge into a
  generic MODS parser.

### D3. Identity cascade keeps the MyCoRe id, not the DOI

`mods_general` takes Investigation.identifier from `harvest_source_id`, then the record's object id, then the DOI.
Reason: `schema_org_general` produces the MyCoRe id for OpenAgrar today. Switching to the DOI would create ~933 new ARCs
and leave the old ones stale until the ARC lifecycle (API#340) exists. Issue #503 suggested "DOI as identifier". This
decision deliberately overrides that suggestion. The DOI is still kept in the ARC (D5).

### D4. Shared safe XML parsing with defusedxml in `middleware.parsing`

Both the list response (protocol) and the object document (parser) are parsed with `defusedxml.ElementTree`, as
`phenoroam_xml` does. Reason: it is the existing shared-parsing convention, and it rejects entity and DTD tricks without
relying on a process-global default parser. Issue #503 suggested the hardened lxml parser. That parser belongs to the
INSPIRE/OWSLib path and is installed only when `middleware.inspire` is imported, so a generic-only process could not
rely on it. The `generic` protocol may import from `middleware.parsing`, so the list parsing can share a small helper
there.

### D5. MODS is mapped directly; field rules live in `docs/mappers/mods.md`

`mods_record` is a Pydantic model in `middleware/payload/mods/`, like `phenoroam`. The mapper reuses the shared helpers
`person_names`, `person_contacts`, `arc_license`, `arc_dates`, `dois` and `identifiers`. DOI, licence, subjects and
DataCite/genre classifications go where the other base mappers put them. Reason: principles.md forbids converting
through another vocabulary, and mapper-docs requires one authoritative doc per productive mapper.

### D6. Politeness is configuration

No new throttling code. The OpenAgrar deployment sets `worker_tasks: 1`, `http.max_connections: 1` and keeps the default
`max_requests_per_second`. That gives one list request plus ~933 object requests in sequence (about 8 minutes at 2
req/s). Reason: the existing knobs already express "one at a time", and per-repository code paths would hide the policy
from operators.

### D7. `page_size` default 1000

The API allows up to 10,000 per page. 1000 keeps each list response small, so a whole OpenAgrar list is one request.
Reason: there is no benefit in larger pages, and a smaller default is kinder to other MyCoRe installations.

## Risks / Trade-offs

- [robots.txt disallows `/api/` and query URLs] → The deployment keeps `http.respect_robots_txt: false`, as it does for
  the Solr path today. OpenAgrar's operators asked for API use (basic#257). Ask them whether to add
  `Allow: /api/v2/objects` (Open question).
- [The API may also go behind the PoW gate or WAF for the cluster IP] → Check from fizz before the draven roll-out. A
  failing list request becomes a repository-level error in the harvest report, not a silent zero.
- [MODS from other MyCoRe instances varies (genres, licence classifications)] → Parser extraction is generic and
  lossless. Interpretation lives in the mapper doc, and RDI deltas can go in `docs/mappers/rdi/` later.
- [ARC content changes for existing OpenAgrar ARCs (richer creators, licence)] → Expected and wanted. Diff the payloads
  of the old and new paths for the same objects before switching (acceptance criterion in #503).
- [`fetch_url` is a new field on a shared type] → Optional, defaults to unset, and only fetching parsers read it.
  Existing protocols are untouched.

## Migration Plan

1. Release the harvester with the new keys. Existing configs are unaffected.
2. In m4.2_infrastructure fizz, switch the `openagrar` entry to `generic.protocol.mycore_rest` (`entry_url` with the two
   `category` filters), `parser.mods_xml` and `mapper.mods_general`, with `worker_tasks: 1` and
   `http.max_connections: 1`. Carsten rolls it out.
3. Compare the fizz run with the previous run: record count (~933), identifiers unchanged, and DOI/licence present.
4. Repeat for draven. Rollback means restoring the previous `openagrar` block. Identity is unchanged, so rollback leaves
   no duplicate ARCs.

## Open Questions

- Will OpenAgrar add `Allow: /api/v2/objects` to robots.txt? This changes only the deployment flag.
- Is `/api/v2/` reachable from the cluster egress IP without the PoW gate? Check on fizz. If not, raise it on basic#257.
