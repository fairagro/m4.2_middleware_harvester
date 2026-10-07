# Tasks

## 1. Remove flat config surface

- [ ] 1.1 Remove `protocol_type`, `sitemap_url`, `http`, and `page_size` fields plus `lift_legacy_flat_protocol` (and
      related warning constants) from `middleware.generic.config.Config`; keep nested `protocol` required; verify
      validating a flat-only dict raises `ValidationError`
- [ ] 1.2 Update `Config` docstring / Field descriptions so they no longer describe a flat lift path; verify wording

## 2. Tests and examples

- [ ] 2.1 Convert generic unit tests that construct Config via flat fields to nested `protocol:`; remove tests whose
      only purpose was flat lift/conflict; verify `uv run pytest middleware/generic/tests` passes
- [ ] 2.2 Update harvester tests that use flat generic config (if any) to nested form; verify
      `uv run pytest middleware/harvester/tests/unit/test_config.py` passes
- [ ] 2.3 Remove the deprecated flat commented example from `dev_environment/config_example.yaml` and trim flat-lift
      wording in `docs/linked_data_to_generic.md`; verify docs no longer present flat `protocol_type` as supported

## 3. Integration

- [ ] 3.1 Run `openspec validate remove-flat-generic-protocol-config` and targeted pytest modules above; verify all pass
