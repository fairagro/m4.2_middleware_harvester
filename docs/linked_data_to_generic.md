# Migrating `linked_data:` repositories to `generic:`

Operator YAML and Helm values should prefer the `generic:` plugin when an equivalent Protocol + PayloadParser pair
exists. `linked_data:` remains supported as a temporary shim (some sitemap types emit deprecation warnings).

## Field mapping

| `linked_data` field               | `generic` equivalent                                                                                                        |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `sitemap_type`                    | Nested key under `protocol:` (`xml`, `mycore_solr`, `regal_find`, …). Deprecated flat form: `protocol_type`.                |
| `sitemap_url`                     | `protocol.<type>.entry_url`. Deprecated flat form: `sitemap_url`.                                                           |
| `dataset_type: html_jsonld`       | Sibling `parser: { type: html_jsonld }`                                                                                     |
| `dataset_type: regal_jsonld`      | Sibling `parser: { type: jsonld }` plus `allowed_context_url` (see below)                                                   |
| `payload_type` (deprecated)       | Sibling `mapper: { type: … }`                                                                                               |
| `http`                            | `protocol.http`                                                                                                             |
| `page_size`                       | `protocol.<type>.page_size` (e.g. mycore_solr / regal_find)                                                                 |
| `resource_base_url`               | `generic.resource_base_url`                                                                                                 |
| `worker_tasks`                    | `generic.worker_tasks`                                                                                                      |
| `jsonld_parse_threshold_bytes`    | `parser.jsonld_parse_threshold_bytes` (and/or `protocol.dcat_ap.jsonld_parse_threshold_bytes`)                              |
| _(new)_ remote JSON-LD `@context` | `parser.allowed_context_url` — exact http(s) IRI; fetched once and cached for the process (transitive `@import` cached too) |

## Canonical shape

```yaml
- rdi: "edal"
  generic:
    protocol:
      xml:
        entry_url: https://doi.ipk-gatersleben.de/sitemap.xml
  parser:
    type: html_jsonld
    allowed_context_url: "https://schema.org/"
  mapper:
    type: schema_org_general
```

Set `allowed_context_url` to the exact `@context` string used by the source (no http/https aliasing). Schema.org HTML
and inline JSON-LD sources need this field; expanded DCAT-AP payloads without a remote `@context` leave it unset.

## Regal / PUBLISSO

`RegalFindProtocol` is available under `generic`. Prefer:

```yaml
parser:
  type: jsonld
  allowed_context_url: "https://frl.publisso.de/context.json"
```

In-repo Publisso examples may still use `linked_data` + `regal_jsonld` until operators flip them; both paths are valid
once `allowed_context_url` is set on the `jsonld` parser.

## Out-of-repo configs

Cluster / ops overlays not in this repository should apply the same mapping when operators next touch those values.
In-repo examples live under `dev_environment/` and `helm/harvester/values.yaml`.
