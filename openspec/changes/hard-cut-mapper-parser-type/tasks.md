# Tasks

## 1. MapperConfig hard-cut

- [ ] 1.1 Replace `MapperConfig.lift_legacy_type_discriminator` with a reject-on-`type` before-validator (clear
      type-as-key pointer); delete `_LEGACY_MAPPER_TYPE_MSG` / lift of flat type-local fields; update docstring — verify
      `uv run pytest middleware/payload/tests/unit/test_data_mapper_registry.py -q` fails until tests updated
- [ ] 1.2 Update payload unit tests: nested form still loads; legacy `{ type: … }` fails with type-as-key mention; no
      warn-and-accept assertions — verify `uv run pytest middleware/payload/tests/unit/test_data_mapper_registry.py -q`
      green

## 2. ParserConfig hard-cut

- [ ] 2.1 Replace `ParserConfig` legacy `type:` lift with reject-on-`type` before-validator; keep
      `_drop_jsonld_only_for_non_jsonld` for nested ignore; delete `_LEGACY_PARSER_TYPE_MSG`; update docstring — verify
      `uv run pytest middleware/parsing/tests/unit/test_parser_config.py -q` fails until tests updated
- [ ] 2.2 Update parser unit tests: nested form still loads; legacy `{ type: … }` (+ flat `allowed_context_url`) fails
      with type-as-key mention; no warn-and-accept — verify
      `uv run pytest middleware/parsing/tests/unit/test_parser_config.py -q` green

## 3. In-repo YAML + gate

- [ ] 3.1 Confirm in-repo Helm / `dev_environment` YAML has no leftover `mapper`/`parser` `type:` discriminators (`rg`
      for legacy shapes); fix only if found — verify grep clean for product YAML
- [ ] 3.2 Run `openspec validate --change hard-cut-mapper-parser-type` and focused pytest for payload + parsing; verify
      green
