## ADDED Requirements

### Requirement: Separate domain logic from technical plumbing
Plugin packages SHALL keep harvest domain logic (discovery semantics, mapping, and record-level error meaning) in domain-oriented modules, and SHALL place concurrency, backpressure, retry, cancellation, and similar mechanics in dedicated infrastructure modules composed by the plugin entrypoint. Plugin entrypoints MAY wire domain callbacks into plumbing modules but MUST NOT embed large asyncio lifecycle, queue, or cancellation blocks alongside mapping rules. Implementations MUST NOT introduce harvester-wide generic frameworks for such plumbing until a second plugin requires the same mechanism.

#### Scenario: Substantial plumbing mixed with domain rules is extracted
- **WHEN** a change adds substantial asyncio queue, semaphore, TaskGroup, or cancellation lifecycle logic in the same module as mapping or dataset-construction rules
- **THEN** that plumbing MUST be moved to a dedicated infrastructure module (or an existing one) and composed through a narrow callback or port interface

#### Scenario: Package-local plumbing until a second consumer exists
- **WHEN** only one plugin needs a given plumbing pattern
- **THEN** the pattern MUST remain inside that plugin package and MUST NOT be promoted to `middleware/harvester` solely for speculative reuse
