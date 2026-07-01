# Schema.org Record Filter

Optional post-fetch filtering for individual datasets in the Schema.org
harvester plugin. Filters are evaluated on structured metadata extracted from
the source record (typically embedded JSON-LD) before graph mapping and ARC
serialization.

Primary use case: two repository entries (e.g. `openagrar` and `thunen`) that
share the same discovery URL but upload to different RDIs based on a metadata
field such as `publisher.name`.

## Requirements

- [ ] The Schema.org plugin `Config` accepts an optional `record_filter`
      object. When omitted, no record-level filtering is applied (current
      behaviour).
- [ ] `record_filter.field` is a required string when `record_filter` is set.
      It uses dot notation to address a value inside the extracted Schema.org
      Dataset object (e.g. `publisher.name`).
- [ ] `record_filter.include` is an optional regular expression string. When
      set, a record is **kept** only if the resolved field value matches the
      pattern (case-insensitive).
- [ ] `record_filter.exclude` is an optional regular expression string. When
      set, a record is **kept** only if the resolved field value does **not**
      match the pattern (case-insensitive).
- [ ] At least one of `include` or `exclude` must be set when `record_filter`
      is present. Setting both applies both rules: the record must match
      `include` (if set) and must not match `exclude` (if set).
- [ ] Invalid regular expressions are rejected at config validation time with
      a clear error (fail fast before harvesting starts).
- [ ] Filtering runs after the dataset payload is fetched and parsed, and
      before `SchemaOrgMapper.map_graph()`.
- [ ] A record that fails the filter yields `SkippedRecord` (not
      `HarvesterError`), with a reason that names the RDI filter field,
      pattern, and resolved value (or `missing`).
- [ ] Filtered records increment `skipped_datasets` in the harvest report.
- [ ] When `record_filter.field` cannot be resolved (missing object, wrong
      type, or empty string), the resolved value is treated as **missing**.
- [ ] A missing field value never matches `include`.
- [ ] A missing field value never matches `exclude` (the record passes an
      exclude-only filter).

## Configuration examples

Thünen entries from OpenAgrar (positive filter):

```yaml
record_filter:
  field: publisher.name
  include: 'Thünen[- ]?Institut|Thuenen Institute|Thünen-Atlas'
```

OpenAgrar entries excluding Thünen (negative filter):

```yaml
record_filter:
  field: publisher.name
  exclude: 'Thünen[- ]?Institut|Thuenen Institute|Thünen-Atlas'
```

## Edge Cases

- `record_filter` omitted → all successfully parsed records proceed to mapping.
- Field resolves to a list → the first non-empty string element is used; if
  none, treat as missing.
- Field resolves to a non-string scalar → coerce with `str()` before regex
  matching.
- Nested field path invalid (e.g. `publisher.name` but `publisher` is a
  string) → treat as missing.
- JSON-LD parse failure before filtering → existing `RecordProcessingError`
  path; filter is not evaluated.
- Duplicate sitemap URL in two repository entries → each entry applies its
  own `record_filter` independently; skipped records are counted per RDI.
