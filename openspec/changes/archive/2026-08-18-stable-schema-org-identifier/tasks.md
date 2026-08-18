## 1. Mapper contract

- [x] 1.1 Add optional `source_url` to `LinkedDataMapper.map_graph` and `RegalMapper.map_graph` (ignored by Regal)
- [x] 1.2 Pass `dataset.identifier` as `source_url` from `LinkedDataPlugin._process_result`

## 2. Schema.org identifier resolution

- [x] 2.1 Extract DOI from literal `schema:identifier` and from `PropertyValue` (`propertyID` doi / identifiers.org, `schema:value`)
- [x] 2.2 Fall back to `schema:url`, `sameAs`, `http(s)` `@id`, then `source_url`; compact MyCoRe `/receive/{id}` to `{id}`
- [x] 2.3 Raise a mapping error when no stable identifier exists; never use blank-node `str(subject)` or title slug for `Investigation.identifier`

## 3. Tests

- [x] 3.1 OpenAgrar JSON-LD without `@id`, PropertyValue DOI → identifier `10.3220/…`; two parses identical
- [x] 3.2 No DOI, Receive-URL `source_url` → MyCoRe id; no DOI/URL/MyCoRe → mapping error, no blank-node identifier
- [x] 3.3 Plugin passes `source_url`; existing Schema.org / Regal / INSPIRE identifier tests still pass

## 4. Validation

- [x] 4.1 `uv run ruff format middleware/` and `uv run pytest middleware/linked_data middleware/inspire -v` for affected packages
