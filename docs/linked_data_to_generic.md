# Migrating `linked_data:` repositories to `generic:`

Operator YAML and Helm values should prefer the `generic:` plugin. `linked_data:` remains supported as a temporary shim
(some sitemap types emit deprecation warnings).

## Field mapping

| `linked_data` field            | `generic` equivalent                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| `sitemap_type`                 | Nested key under `protocol:` (`xml`, `mycore_solr`, `regal_find`, …). Deprecated flat form: `protocol_type`.     |
| `sitemap_url`                  | `protocol.<type>.entry_url`. Deprecated flat form: `sitemap_url`.                                                |
| `dataset_type: html_jsonld`    | Sibling `parser: { type: html_jsonld }`                                                                          |
| `dataset_type: regal_jsonld`   | Sibling `parser: { type: jsonld }` (inline JSON-LD from `/find`)                                                 |
| `payload_type` (deprecated)    | Sibling `mapper: { type: … }`                                                                                    |
| `http`                         | `protocol.http`                                                                                                  |
| `page_size`                    | `protocol.<type>.page_size` (mycore_solr / regal_find)                                                           |
| `resource_base_url`            | `generic.resource_base_url`                                                                                      |
| `worker_tasks`                 | `generic.worker_tasks`                                                                                           |
| `jsonld_parse_threshold_bytes` | `parser.jsonld_parse_threshold_bytes` (and/or `protocol.dcat_ap.jsonld_parse_threshold_bytes` for catalog pages) |

## Canonical shape

```yaml
- rdi: "edal"
  generic:
    protocol:
      xml:
        entry_url: https://doi.ipk-gatersleben.de/sitemap.xml
  parser:
    type: html_jsonld
  mapper:
    type: schema_org_general
```

MyCoRe Solr and Regal `/find` use the same nesting (`protocol.mycore_solr` / `protocol.regal_find`). Shared HTTP
settings live under `protocol.http`.

Deprecated flat `generic` keys (`protocol_type` + `sitemap_url`) still lift with a warning; prefer the nested form
above.

## Out-of-repo configs

Cluster / ops overlays not in this repository should apply the same mapping when operators next touch those values.
In-repo examples live under `dev_environment/` and `helm/harvester/values.yaml`.
