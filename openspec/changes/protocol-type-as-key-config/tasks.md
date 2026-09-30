## 1. Config models

- [x] 1.1 Add `XmlProtocolConfig` / `MycoreSolrProtocolConfig` on the Protocol modules plus shared `ProtocolConfig`
      (shared `http`, type-as-key children, exactly-one validator, `protocol_type` / `type_config` helpers) — verify
      with unit tests for valid nested XML/Solr and reject 0/2 type keys
- [x] 1.2 Restructure `generic.Config`: nested `protocol`; deprecate flat `protocol_type` / `sitemap_url` / `http` /
      `page_size`; lift + conflict validator; derive `effective_resource_base_url` from `entry_url` — verify lift
      warning tests and conflict failure
- [x] 1.3 Update harvester `RepositoryConfig` protocol registry check + `source_url` to use nested protocol after lift —
      verify existing generic config tests still pass (flat) and add nested case

## 2. Protocol + plugin wiring

- [x] 2.1 Remove `SupportsSitemapUrl`; Protocol/`XmlProtocol`/`MycoreSolrProtocol` take type settings and use
      `entry_url` — verify mycore_solr + registry unit tests
- [x] 2.2 Update `GenericPlugin` to build client from `protocol.http` and construct Protocol from type settings — verify
      generic plugin unit tests
- [x] 2.3 Update linked_data `MycoreSolrSitemap` shim to adapt flat `sitemap_url`/`page_size` into
      `MycoreSolrProtocolConfig` — verify linked_data mycore_solr tests

## 3. Docs / examples / specs sync

- [x] 3.1 Update `dev_environment/config_example.yaml` (and any generic demo snippet) to show nested `protocol:` while
      leaving deprecated flat comments if useful — verify YAML still validates via config load test or manual
      model_validate
- [x] 3.2 Align main `openspec/specs/{harvest-protocol,generic-harvesting,sitemap-mycore-solr,harvester-configuration}`
      wording with this change’s deltas where the working tree already diverged for #293 — verify
      `openspec validate --changes protocol-type-as-key-config`
