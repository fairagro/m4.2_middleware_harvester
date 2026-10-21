## ADDED Requirements

### Requirement: Reject sitemap_type mycore_solr under linked_data

The system SHALL NOT accept `linked_data.sitemap_type: mycore_solr`. Config load for such a repository MUST fail
validation. Other `sitemap_type` values (`xml`, `regal_find`) are unaffected. MyCoRe Solr discovery MUST use
`generic.protocol.mycore_solr` with sibling `parser` and `mapper`.

#### Scenario: mycore_solr linked_data path is rejected

- **WHEN** a linked_data repository sets `sitemap_type: mycore_solr`
- **THEN** configuration validation fails

#### Scenario: Other sitemap types remain valid

- **WHEN** a linked_data repository sets `sitemap_type` to `xml` or `regal_find`
- **THEN** validation does not fail for that reason alone

## REMOVED Requirements

### Requirement: Deprecate sitemap_type mycore_solr under linked_data

**Reason:** Soft-deprecation replaced by hard rejection (#396).

**Migration:** Use nested `generic.protocol.mycore_solr` instead of `linked_data.sitemap_type: mycore_solr`.
