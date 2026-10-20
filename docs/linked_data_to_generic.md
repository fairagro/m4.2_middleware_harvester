# Migrating `linked_data:` repositories to `generic:`

Operator YAML and Helm values should prefer the `generic:` plugin when an equivalent Protocol + PayloadParser pair
exists. The `linked_data:` plugin key is **deprecated** (config load emits a `logger.warning`); it remains a temporary
shim until a later hard cut. Nested legacy fields (e.g. `sitemap_type: mycore_solr`) may emit additional warnings.

Mapper and parser selection use **type-as-key** (same idiom as `generic.protocol`). Deprecated flat
`mapper: { type: … }` / `parser: { type: … }` still lift with a warning until the hard-cut follow-up. This guide does
**not** invent type-as-key under the deprecated `linked_data:` plugin key — migrate to `generic:` instead.

## Field mapping

| `linked_data` field               | `generic` equivalent                                                                                                                                                                                                                                                                                                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sitemap_type`                    | Nested key under `protocol:` (`xml`, `mycore_solr`, `regal_find`, …).                                                                                                                                                                                                                                                                                                                                                     |
| `sitemap_url`                     | `protocol.<type>.entry_url`.                                                                                                                                                                                                                                                                                                                                                                                              |
| `dataset_type: html_jsonld`       | Sibling `parser: { html_jsonld: { … } }`                                                                                                                                                                                                                                                                                                                                                                                  |
| `dataset_type: regal_jsonld`      | Sibling `parser: { jsonld: { allowed_context_url: … } }`                                                                                                                                                                                                                                                                                                                                                                  |
| `payload_type` (deprecated)       | Sibling `mapper: { <mapper_type>: { … } }`                                                                                                                                                                                                                                                                                                                                                                                |
| `http`                            | `protocol.http`                                                                                                                                                                                                                                                                                                                                                                                                           |
| `page_size`                       | `protocol.<type>.page_size` (e.g. mycore_solr / regal_find)                                                                                                                                                                                                                                                                                                                                                               |
| `resource_base_url`               | `generic.resource_base_url` (Regal may also set `mapper.regal_general.resource_base_url`)                                                                                                                                                                                                                                                                                                                                 |
| `worker_tasks`                    | `generic.worker_tasks`                                                                                                                                                                                                                                                                                                                                                                                                    |
| `jsonld_parse_threshold_bytes`    | `parser.<jsonld\|html_jsonld>.jsonld_parse_threshold_bytes` (and/or `protocol.dcat_ap.jsonld_parse_threshold_bytes`)                                                                                                                                                                                                                                                                                                      |
| _(new)_ remote JSON-LD `@context` | `parser.<jsonld\|html_jsonld>.allowed_context_url` — http(s) IRI or list of IRIs to pin (trailing-slash-insensitive; `http` also matches `https`); fetched once and cached for the process (transitive `@import` cached too). Cache size: top-level `jsonld_context_cache_max_entries` (default 64). When unset on `jsonld`/`html_jsonld`, config load warns and remotes are still fetched (legacy configs keep working). |

## Canonical shape

```yaml
- rdi: "edal"
  generic:
    protocol:
      xml:
        entry_url: https://doi.ipk-gatersleben.de/sitemap.xml
  parser:
    # string or list; trailing slashes ignored; http pin also accepts https
    html_jsonld:
      allowed_context_url: "http://schema.org"
  mapper:
    schema_org_general: {}
```

Prefer setting `allowed_context_url` to the `@context` IRI(s) used by the source (string or YAML list; trailing slashes
are ignored when matching). An `http` pin also accepts the same IRI under `https`; the reverse does not hold — pin
`http://schema.org` for sources like e!DAL / PlabiPD. When the field is omitted on a JSON-LD parser, config load logs a
warning and absolute http(s) remote contexts are still downloaded via polite HTTP and cached (size-bounded). Expanded
DCAT-AP payloads without a remote `@context` can leave it unset (you will still see the config warning for `jsonld` /
`html_jsonld`).

## Regal / PUBLISSO

`RegalFindProtocol` is available under `generic`. In-repo examples (`dev_environment/config.all-rdis.yaml`,
`helm/harvester/values.yaml`) use:

```yaml
- rdi: "publisso"
  generic:
    protocol:
      http:
        respect_robots_txt: false
      regal_find:
        entry_url: "https://frl.publisso.de/find"
    resource_base_url: "https://repository.publisso.de/resource/"
  parser:
    jsonld:
      allowed_context_url: "https://frl.publisso.de/context.json"
  mapper:
    regal_general: {}
```

Prefer pinning `allowed_context_url` on the `jsonld` parser; omitting it still works (config-load warning; remotes still
fetched).

## Out-of-repo configs

Cluster / ops overlays not in this repository should apply the same mapping when operators next touch those values.
In-repo examples live under `dev_environment/` and `helm/harvester/values.yaml`.
