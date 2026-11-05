# Tasks

## 1. MapperConfig hard-cut

- [x] 1.1 Delete `MapperConfig.lift_legacy_type_discriminator` / `_LEGACY_MAPPER_TYPE_MSG` (no replacement reject
      validator — leftover `type:` fails via `extra="forbid"`); update docstring — verify focused payload tests
- [x] 1.2 Update payload unit tests: nested form still loads; legacy `{ type: … }` fails as extra input; no
      warn-and-accept assertions — verify `uv run pytest middleware/payload/tests/unit/test_data_mapper_registry.py -q`
      green

## 2. ParserConfig hard-cut

- [x] 2.1 Delete `ParserConfig` legacy `type:` lift / `_LEGACY_PARSER_TYPE_MSG` (keep JSON-LD ignore-drop only); update
      docstring — verify focused parser tests
- [x] 2.2 Update parser unit tests: nested form still loads; legacy `{ type: … }` fails as extra input; no
      warn-and-accept — verify `uv run pytest middleware/parsing/tests/unit/test_parser_config.py -q` green

## 3. In-repo YAML + gate

- [x] 3.1 Confirm in-repo Helm / `dev_environment` YAML has no leftover `mapper`/`parser` `type:` discriminators (`rg`
      for legacy shapes); fix only if found — verify grep clean for product YAML
- [x] 3.2 Run `openspec validate --change hard-cut-mapper-parser-type` and focused pytest for payload + parsing; verify
      green
