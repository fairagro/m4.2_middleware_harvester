# Proposal

## Why

OpenAgrar asked us to stop scraping HTML record pages and use their MyCoRe REST API instead (basic-middleware #257).
Record pages are expensive to render and contributed to a ~75 min outage; the shared egress IP was removed from the WAF
allow list, so `/receive/` traffic risks the proof-of-work gate again (#271). Today we discover via Solr (`mycore_solr`)
and parse Schema.org JSON-LD from HTML — operators want a gentler path over `/api/v2/objects` with MODS XML.

## What Changes

- Add generic protocol `mycore_rest`: discover published objects via MyCoRe REST list (`entry_url` with category
  filters), page with `after_id`, yield one record URL per `mycoreobject` id (REST object URL, not `/receive/`).
- Add parser `mods_xml`: extract `mods:mods` from MyCoRe object XML using the hardened lxml parser.
- Add mapper `mods_general` (+ `docs/mappers/mods.md`): MODS → ARC covering at least today’s `schema_org_general`
  OpenAgrar fields, plus DOI and licence.
- Wire OpenAgrar example / fixture config to `mycore_rest` + `mods_xml` + `mods_general` (no Solr, no `/receive/` in the
  new path).

**Non-goals**

- Incremental harvest via `modified_after` / harvest state (follow-up).
- Removing production Solr + `html_jsonld` overlays in infrastructure (cutover after deploy).
- OpenAgrar-only hardcoding in protocol/parser/mapper code (keep reusable for other MyCoRe RDIs).

## Capabilities

### New Capabilities

- `mycore-rest`: Generic protocol for MyCoRe REST `api/v2/objects` discovery and record URL yield.
- `mods-xml-parser`: Parse MyCoRe object XML into a MODS-backed payload kind for the shared parser registry.
- `mods-to-arc-mapping`: Map MODS payloads to ARC (`mods_general` + mapper doc).

### Modified Capabilities

- `payload`: Add `PayloadKind` for MODS records and register `mods_general` DataMapper.
- `payload-parser`: Register shared `mods_xml` parser key for URL-fetched MyCoRe object XML.
- `harvester-configuration`: Nested `protocol.mycore_rest` / `parser.mods_xml` / mapper `mods_general` typing as needed.
- `mapper-docs`: Index / layout entry for the new MODS base mapper doc.
- `generic-harvesting`: Acknowledge `mycore_rest` as a supported generic protocol type (if the parent spec enumerates
  protocols).

## Impact

- `middleware/generic` (new protocol), `middleware/parsing` (new parser + payload kind wiring), `middleware/payload`
  (new DataMapper), `docs/mappers/mods.md`, OpenAgrar fixtures / `config_example` / demo config.
- Issue #503; related #271, #464, basic-middleware #257.
