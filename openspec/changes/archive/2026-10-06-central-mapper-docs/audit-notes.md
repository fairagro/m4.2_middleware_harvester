# Mapping docs audit notes (#170 / central-mapper-docs)

Behaviour oracle: mapper code + unit tests. Fixes applied in this change unless noted.

## Schema.org

| Finding                                                                                    | Resolution                                                 |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Doc pointed at removed linked_data `_KNOWN_EXTENSION_CONTEXTS` path                        | Doc → `parser.allowed_context_url` / jsonld-context-loader |
| Spec multi-Dataset scenario mentioned page URL when multi-Dataset forbids harvest/page ids | Spec scenario clarified                                    |
| Mapper module docstring still said “EXAMPLE IMPLEMENTATION”                                | Docstring updated                                          |

## Regal

| Finding                                                               | Resolution                                                   |
| --------------------------------------------------------------------- | ------------------------------------------------------------ |
| Spec edge-case still said no-comma `prefLabel` → LastName-only Person | Spec rewritten; given-name requirement remains authoritative |
| Doc (and code) used `"Untitled"` when title and prefLabel were empty  | Fail closed — no placeholder; principles + spec + tests      |
| Doc said `associatedPublication` → Publication or Comment             | Doc → Comment only                                           |
| Doc listed first-class `Medium` / `Last Modified By`                  | Doc → opaque-only today                                      |

## INSPIRE

| Finding                                                        | Resolution                                                    |
| -------------------------------------------------------------- | ------------------------------------------------------------- |
| Doc said series ignored                                        | Doc → series harvested/mapped; Hierarchy Level comment        |
| Spec said Data Processing on Assay                             | Spec → Study hosts Data Processing; Assay is Measurement      |
| Doc Study title `"Study for: …"` / `{id}_study` / `{id}_assay` | Doc → title slug / fileIdentifier; Study title = record.title |
| Doc keywords, charset, acquisition→TechnologyPlatform          | Doc → not mapped / hardcoded platform                         |

## RDI overlays

No separate overlay mapper types or `builds_on` classes in code; shipped configs use base `mapper.type` values only.
`docs/mappers/rdi/` left empty (README naming guidance only).

## Deferred behaviour (linked issue)

Implementing INSPIRE keywords/charset/acquisition extraction and first-class Regal `medium` / `lastModifiedBy` would
change mapper behaviour — tracked as linked follow-up
[#441](https://github.com/fairagro/m4.2_middleware_harvester/issues/441), not in this docs PR.
