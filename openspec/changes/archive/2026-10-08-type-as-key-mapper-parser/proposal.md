# Proposal

## Why

`generic.protocol` already uses type-as-key (shared fields as siblings of a single type-named child). Repository
`mapper:` and `parser:` still use a parallel `type:` discriminator plus mixed shared/type-specific fields, so operators
see two config shapes for the same idea. Aligning mapper/parser to type-as-key removes that inconsistency while keeping
existing `{ type: … }` YAML working through a deprecation window (#384).

## What Changes

- Redesign repository `mapper:` to type-as-key: shared fields (e.g. `placeholders`) as siblings of exactly one
  type-named child (`schema_org_general`, `regal_general`, `inspire_general`, `phenoroam_general`, `ckanext_dcat`);
  type-specific fields live under that child (`resource_base_url`, `catalog_name` / `catalog_url`, …)
- Redesign repository `parser:` the same way: exactly one type-named child (`html_jsonld`, `jsonld`, `phenoroam_xml`, …)
  holding parser-specific fields (`allowed_context_url`, `jsonld_parse_threshold_bytes`, …)
- **Soft-deprecate** legacy `{ type: … }` (+ flat sibling settings): accept with lift into nested form and emit
  `logger.warning` pointing at the type-as-key shape; do **not** fail validation solely for using `type:`
- Migrate in-repo YAML / Helm examples to nested form
- Update OpenSpec for harvester configuration, payload, and payload-parser contracts
- Open a follow-up Task for the hard-cut removal of the legacy `type:` discriminator
  ([#478](https://github.com/fairagro/m4.2_middleware_harvester/issues/478))

## Non-goals

- Reshaping `linked_data` `sitemap_type` / `dataset_type` into type-as-key (prefer migrate to `generic`; tracked via
  linked_data hard-cut #467)
- Hard-removing `{ type: … }` in this change (follow-up issue)
- Changing DataMapper / PayloadParser registry keys or mapping behaviour beyond config surface

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `harvester-configuration`: Canonical `mapper` / `parser` are type-as-key; legacy `{ type: … }` lifts with warning
- `payload`: Mapper selection wording uses type-as-key (legacy `mapper.type` accepted as deprecated lift)
- `payload-parser`: Parser selection wording uses type-as-key (legacy `parser.type` accepted as deprecated lift)

## Impact

- **Issue:** #384; follow-up hard-cut [#478](https://github.com/fairagro/m4.2_middleware_harvester/issues/478)
- **Code:** `middleware/payload/mapper_config.py`, `middleware/parsing/parser_config.py`, harvester validation /
  accessors that read `mapper.type` / `parser.type`, unit tests
- **Ops:** Warning-only for legacy YAML; in-repo configs flipped to nested
- **Out of scope:** `linked_data` discovery type-as-key; hard delete of `type:`
