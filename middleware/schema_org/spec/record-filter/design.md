# Schema.org Record Filter — Design

## Architecture overview

Filtering is a plugin-level concern in `SchemaOrgPlugin._process_result()`,
inserted after `Dataset.to_graph()` payload extraction and before
`SchemaOrgMapper.map_graph()`:

```text
discover URL
  → fetch + parse (Dataset)
  → extract Schema.org Dataset dict from JSON-LD
  → RecordFilter.evaluate(dict)  → SkippedRecord | continue
  → rdflib Graph + mapper → ARC JSON
```

```text
Config.record_filter (optional)
        │
        ▼
RecordFilter ──resolve field path──► str | missing
        │
        ├── include regex (optional, re.IGNORECASE)
        └── exclude regex (optional, re.IGNORECASE)
        │
        ▼
   pass → map_graph
   fail → SkippedRecord
```

Each repository entry carries its own `record_filter`; the orchestrator RDI
is unchanged. Two entries may share the same `sitemap_url` with complementary
include/exclude patterns (OpenAgrar / Thünen split).

## Key Decisions

1. **Filter on extracted JSON-LD Dataset dict, not on the RDF graph or Solr
   discovery index**
   — The OpenAgrar / Thünen split in production is defined on
   `publisher.name` in Schema.org JSON-LD (as in `openagar.json` /
   `thuenen_atlas.json`). Solr `mods.name` can match creator affiliations and
   is blocked by OpenAgrar PoW for ad-hoc CLI tests. Post-fetch JSON-LD
   filtering matches the Basic Middleware regex semantics and avoids false
   positives from indexed author names.

2. **`field` is a configurable dot-path string, defaulting to no implicit
   field when `record_filter` is absent**
   — Dot notation (`publisher.name`) covers the Thünen use case without a
   hard-coded field name. Resolution walks nested dict keys left-to-right; no
   JSONPath dependency. Lists at an intermediate segment use the first element;
   a string leaf at `publisher` when the path expects `publisher.name` yields
   missing.

3. **Separate optional `include` and `exclude` regex strings, not a single
   `mode` enum**
   — OpenAgrar needs exclude-only; Thünen needs include-only. Two optional
   keys express both without duplicating config types. When both are set,
   include is applied first conceptually (must match), then exclude (must not
   match). Pydantic validates that at least one is present.

4. **Case-insensitive matching via `re.IGNORECASE` (fixed, not configurable)**
   — Publisher strings vary in casing (`Thünen-Institut`, `Thuenen Institute`).
   A config flag would add noise; case-insensitivity matches Basic Middleware
   and the analysed harvest files.

5. **Missing field values fail include and pass exclude-only**
   — Of 52 records in `openagar.json` without `publisher`, none are Thünen.
   Exclude-only OpenAgrar keeps them; include-only Thünen skips them. Failing
   include on missing avoids uploading under the wrong RDI when metadata is
   incomplete.

6. **`SkippedRecord` for filter rejection, not silent drop or error**
   — Consistent with `spec/skipped-datasets/`. Operators see
   `fairagro:skippedDatasets` per RDI and INFO logs with reason + URL. Filter
   skips are intentional, not failures.

7. **Compile regexes at config validation time**
   — `RecordFilterConfig` uses a Pydantic `@field_validator` (or model
   validator) to compile `include` / `exclude` with `re.compile(...,
   re.IGNORECASE)` and surface `re.error` as `ValidationError`. Avoids
   mid-harvest failures on typo patterns.

8. **Extract Dataset dict helper shared between filter and tests**
   — `HtmlJsonLdDataset` already parses JSON-LD blocks; the filter reuses the
   same “find `@type`: Dataset object” selection logic (first Dataset in
   merged blocks, or sole object). Keeps filter tests independent of HTTP.

## Config model (sketch)

```python
class RecordFilterConfig(BaseModel):
    field: str = Field(min_length=1)
    include: str | None = None
    exclude: str | None = None

    @model_validator(mode="after")
    def at_least_one_pattern(self) -> Self: ...

    @field_validator("include", "exclude")
    @classmethod
    def compile_regex(cls, v: str | None) -> str | None: ...
```

Added as `record_filter: RecordFilterConfig | None = None` on
`middleware.schema_org.config.Config`.

## Field resolution algorithm

Given `field = "publisher.name"` and dataset dict `d`:

1. Split on `.`.
2. For each segment, if current value is `dict`, take `value[segment]`.
3. If current value is `list`, take first element and continue.
4. If any step fails, return `missing`.
5. Final value: if `str`, strip; empty → `missing`; else `str(value)`.

## OpenAgrar / Thünen deployment pattern

| RDI | `include` | `exclude` | Expected effect (current harvest files) |
| --- | --------- | --------- | ----------------------------------------- |
| `thunen` | Thünen regex | — | 49 kept, 775+ skipped when sharing full index |
| `openagrar` | — | Thünen regex | 775 kept, 49 skipped |

Both entries use the same `sitemap_url` and `sitemap_type: mycore_solr`; only
`record_filter` and `rdi` differ. HTTP cost is doubled for shared discovery
unless Solr pre-filtering is added later as a separate optimisation.

## Non-goals

- Solr-side or sitemap-level filtering (out of scope; see
  `sitemap-mycore-solr/`).
- Filtering on ARC or RO-Crate fields after mapping.
- JSONPath, XPath, or multi-field boolean expressions (YAGNI; dot-path +
  include/exclude suffices for Thünen).
