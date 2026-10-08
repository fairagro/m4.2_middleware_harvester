# Design

## Context

See proposal.md — Why. Only `CkanextDcatMapper` reads the fields; only SRADI sets them.

## Decisions

1. **Warn in `MapperConfig`, not in the mapper** — Config load is the operator-facing surface (same pattern as the
   `linked_data` deprecations in `RepositoryConfig`). Operators validating config without harvesting still see it.
2. **No `Field(deprecated=True)`** — pydantic would raise `DeprecationWarning` on every attribute read, including the
   mapper's own `from_config` during the window. The description and `logger.warning` carry the signal.
3. **Blank values do not warn** — they are already normalized to unset by the existing validators.
4. **Hard removal stays out of this change** — tracked in #471.

## Risks / Trade-offs

- [Dev environment loses `Data Catalog` comment] → Equivalent provenance comes from the API's `known_rdis` RDI comments.
- [Operators ignore the warning] → Follow-up removal forces migration.
