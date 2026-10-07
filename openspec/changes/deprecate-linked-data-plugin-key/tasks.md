# Tasks

## 1. Deprecation warning

- [ ] 1.1 Add a `RepositoryConfig` validator that emits `logger.warning` whenever `linked_data` is set, with copy
      pointing at `generic` + nested protocol / sibling parser/mapper (and that the shim will be removed later); verify
      a unit test with `caplog` asserts the warning and that validation still succeeds
- [ ] 1.2 Confirm `generic`-only repositories do not emit this plugin-key warning; verify via unit test

## 2. In-repo YAML flip (Publisso / Regal)

- [ ] 2.1 Migrate `dev_environment/config.all-rdis.yaml` Publisso entry from `linked_data` to
      `generic.protocol.regal_find` + `parser.type: jsonld` with `allowed_context_url` for the FRL context; verify the
      file has no `linked_data:` Publisso block and that `RepositoryConfig` / full config load accepts the entry
- [ ] 2.2 Migrate `helm/harvester/values.yaml` `example-publisso-regal` the same way; verify comments no longer present
      `linked_data` as the preferred path for that example
- [ ] 2.3 Update `docs/linked_data_to_generic.md` (and any example comments) so in-repo examples are described as
      preferring `generic`; verify the Regal section matches the flipped YAML

## 3. Integration check

- [ ] 3.1 Run targeted harvester config unit tests (`uv run pytest middleware/harvester/tests/unit/test_config.py`) and
      verify they pass
