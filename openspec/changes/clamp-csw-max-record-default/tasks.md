# Tasks

## 1. Capabilities + client clamp

- [ ] 1.1 Replace warn-only `warn_if_server_caps_page_size` with clamp/log helper(s) that return or expose the
      advertised positive `MaxRecordDefault` and emit at most one INFO when clamping; update `test_capabilities.py`
      (clamp + silent paths) and verify `uv run pytest middleware/inspire/tests/unit/test_capabilities.py -v` passes
- [ ] 1.2 On `CSWClient` connect, store advertised cap; apply `min(effective_page_size, advert)` for default
      `chunk_size` paging and after XML `maxRecords` resolution in `_prepare_xml_paging`; update/add unit tests for
      `chunk_size` clamp, XML-above-advert clamp, XML-below-advert no-clamp, and absent advert; verify focused
      `uv run pytest middleware/inspire/tests/unit/test_capabilities.py middleware/inspire/tests/unit/test_csw_client_paging.py -v`
      passes
- [ ] 1.3 Rewrite `openspec/specs/csw-harvesting/design.md` decision 6 to describe clamp-down + INFO (no
      warn-without-clamp); verify the text matches the delta requirement

## 2. Quality gate

- [ ] 2.1 Format/check touched Python with `uv run ruff format --config ruff.toml` /
      `uv run ruff check --config ruff.toml` on the edited inspire files and verify
      `openspec validate --change clamp-csw-max-record-default` succeeds
