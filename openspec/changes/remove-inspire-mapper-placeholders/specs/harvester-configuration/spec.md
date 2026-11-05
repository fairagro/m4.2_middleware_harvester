## REMOVED Requirements

### Requirement: mapper.placeholders on inspire repositories is deprecated

**Reason:** Soft-lift of `mapper.placeholders` → `inspire.placeholders` removed after the migration window (#477).

**Migration:** Set placeholders under `inspire.placeholders` only. Do not rely on lift or a dedicated reject of leftover
`mapper.placeholders` on inspire repositories. `mapper.placeholders` remains valid for `generic` / `oai_pmh`.
