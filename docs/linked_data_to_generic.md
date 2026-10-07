# Migrating `linked_data:` repositories to `generic:`

Operator YAML and Helm values should prefer the `generic:` plugin when an equivalent Protocol + PayloadParser pair
exists. `linked_data:` remains supported as a temporary shim (some sitemap types emit deprecation warnings).

## Field mapping

| `linked_data` field               | `generic` equivalent                                                                                                                                                                                                                                                                                                                                                                                |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sitemap_type`                    | Nested key under `protocol:` (`xml`, `mycore_solr`, `regal_find`, …).                                                                                                                                                                                                                                                                                                                               |
| `sitemap_url`                     | `protocol.<type>.entry_url`.                                                                                                                                                                                                                                                                                                                                                                        |
| `dataset_type: html_jsonld`       | Sibling `parser: { type: html_jsonld }`                                                                                                                                                                                                                                                                                                                                                             |
| `dataset_type: regal_jsonld`      | Sibling `parser: { type: jsonld }` plus `allowed_context_url` (see below)                                                                                                                                                                                                                                                                                                                           |
| `payload_type` (deprecated)       | Sibling `mapper: { type: … }`                                                                                                                                                                                                                                                                                                                                                                       |
| `http`                            | `protocol.http`                                                                                                                                                                                                                                                                                                                                                                                     |
| `page_size`                       | `protocol.<type>.page_size` (e.g. mycore_solr / regal_find)                                                                                                                                                                                                                                                                                                                                         |
| `resource_base_url`               | `generic.resource_base_url`                                                                                                                                                                                                                                                                                                                                                                         |
| `worker_tasks`                    | `generic.worker_tasks`                                                                                                                                                                                                                                                                                                                                                                              |
| `jsonld_parse_threshold_bytes`    | `parser.jsonld_parse_threshold_bytes` (and/or `protocol.dcat_ap.jsonld_parse_threshold_bytes`)                                                                                                                                                                                                                                                                                                      |
| _(new)_ remote JSON-LD `@context` | `parser.allowed_context_url` — http(s) IRI or list of IRIs to pin (trailing-slash-insensitive; `http` also matches `https`); fetched once and cached for the process (transitive `@import` cached too). Cache size: top-level `jsonld_context_cache_max_entries` (default 64). When unset on `jsonld`/`html_jsonld`, config load warns and remotes are still fetched (legacy configs keep working). |

## Canonical shape

```yaml
- rdi: "edal"
  generic:
    protocol:
      xml:
        entry_url: https://doi.ipk-gatersleben.de/sitemap.xml
  parser:
    type: html_jsonld
    # string or list; trailing slashes ignored; http pin also accepts https
    allowed_context_url: "http://schema.org"
  mapper:
    type: schema_org_general
```

Prefer setting `allowed_context_url` to the `@context` IRI(s) used by the source (string or YAML list; trailing slashes
are ignored when matching). An `http` pin also accepts the same IRI under `https`; the reverse does not hold — pin
`http://schema.org` for sources like e!DAL / PlabiPD. When the field is omitted on a JSON-LD parser, config load logs a
warning and absolute http(s) remote contexts are still downloaded via polite HTTP and cached (size-bounded). Expanded
DCAT-AP payloads without a remote `@context` can leave it unset (you will still see the config warning for `jsonld` /
`html_jsonld`).

## Regal / PUBLISSO

`RegalFindProtocol` is available under `generic`. Prefer:

```yaml
parser:
  type: jsonld
  allowed_context_url: "https://frl.publisso.de/context.json"
```

In-repo Publisso examples may still use `linked_data` + `regal_jsonld` until operators flip them. Prefer pinning
`allowed_context_url` on the `jsonld` parser; omitting it still works (config-load warning; remotes still fetched).

## Out-of-repo configs

Cluster / ops overlays not in this repository should apply the same mapping when operators next touch those values.
In-repo examples live under `dev_environment/` and `helm/harvester/values.yaml`.
