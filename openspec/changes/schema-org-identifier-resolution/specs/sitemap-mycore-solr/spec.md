## MODIFIED Requirements

### Requirement: Yield one UrlDiscoveryResult per unique constructed URL

The system SHALL yield one `UrlDiscoveryResult` per unique constructed URL. Each result MUST set `identifier` (and `url`) to the constructed Receive-URL and MUST set `harvest_source_id` to the Solr document `id` value used to build that URL.

#### Scenario: MyCoRe Solr id is forwarded as harvest source id

- **WHEN** a Solr document has `id` `openagrar_mods_0001` and the constructed URL is `https://www.openagrar.de/receive/openagrar_mods_0001`
- **THEN** the yielded `UrlDiscoveryResult` MUST have `harvest_source_id` `openagrar_mods_0001`
