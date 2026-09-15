## MODIFIED Requirements

### Requirement: Select mapper by payload_type

The system SHALL select mapper implementations using configured repository `mapper.type` values via the shared
`middleware.payload` DataMapper registry (explicit, non-guessing selection). Vocabulary-specific Linked Data mappers MUST
live in `middleware.payload` and register against that registry. Behavioural ARC mapping rules for Schema.org and Regal
are unchanged (including ResourceView / StableGraph requirements in this spec).

#### Scenario: Configured mapper type selects the registered mapper

- **WHEN** repository config sets a supported `mapper.type` for a linked-data harvest
- **THEN** registry resolution returns the matching concrete mapper from `middleware.payload`

### Requirement: Keep mapping separate from discovery

The system SHALL keep mapping logic separate from sitemap discovery and dataset payload extraction. Mapping code MUST
reside in `middleware.payload` and MUST NOT import protocol clients (sitemap/CSW/OAI HTTP discovery).

#### Scenario: Mapper does not fetch sitemaps

- **WHEN** a mapper implementation runs
- **THEN** it operates only on an already-built RDF graph (via `ParsedPayload` or `map_graph`) and does not perform
  sitemap discovery or HTTP dataset fetch

### Requirement: Edge case — no runtime config outside payload selection

The system SHALL keep mapper runtime configuration limited to fields needed for the selected `mapper.type` (e.g. Regal
resource base URL via mapper or repository mapper config). Discovery/plugin fields MUST NOT leak into StableGraph wrap.

#### Scenario: Mapper-specific config only

- **WHEN** a repository selects a given `mapper.type`
- **THEN** only configuration relevant to that mapper type influences mapping behaviour beyond the graph and
  `MappingContext`
