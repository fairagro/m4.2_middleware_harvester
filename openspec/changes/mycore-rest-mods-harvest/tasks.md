# Tasks

## 1. Protocol `mycore_rest`

- [ ] 1.1 Add `ProtocolType.mycore_rest` + config (`entry_url`, `page_size`) and register `MycoreRestProtocol`
- [ ] 1.2 Implement list fetch/paging (`after_id`), yield REST object `UrlDiscoveryResult`s; unit tests with fixture XML
- [ ] 1.3 Optional `get_expected_count` from `X-Total-Count` when present

## 2. Parser `mods_xml` + payload kind

- [ ] 2.1 Add `PayloadKind.mods_record` and a structured MODS record model (or agreed intermediate)
- [ ] 2.2 Implement `mods_xml` PayloadParser (fetch object XML, hardened lxml, extract `mods:mods`); register parser
- [ ] 2.3 Unit tests: happy path, missing MODS, client required, entity-hardening smoke

## 3. Mapper `mods_general` + docs

- [ ] 3.1 Write `docs/mappers/mods.md` (Identity · Investigation · Study · Assay · Contacts · Fallbacks · Refusal)
- [ ] 3.2 Implement and register `mods_general` DataMapper; unit tests for DOI/licence/title/creators parity bar
- [ ] 3.3 Update `docs/mappers/README.md` index for MODS

## 4. Config, fixtures, OpenAgrar example

- [ ] 4.1 Wire harvester/generic config validation for nested `mycore_rest` / `mods_xml` / `mods_general`
- [ ] 4.2 Extend OpenAgrar fixtures for REST list + object paths; example/demo config using the new stack (no Solr /
      `/receive/` on that path)
- [ ] 4.3 Run focused unit tests + `openspec validate mycore-rest-mods-harvest`
