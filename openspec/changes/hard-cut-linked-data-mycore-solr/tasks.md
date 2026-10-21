# Tasks

## 1. linked_data: remove enum + shim

- [ ] 1.1 Remove `SitemapType.mycore_solr` from `middleware/linked_data/.../config.py` (and field description that marks
      it deprecated); verify a unit test shows `sitemap_type: mycore_solr` fails Config / RepositoryConfig validation
- [ ] 1.2 Delete `middleware/linked_data/.../sitemap/mycore_solr.py`, unregister it from the sitemap registry /
      `__init__` imports, and drop any linked_data tests that only exercised the shim; verify no remaining imports of
      `MycoreSolrSitemap` under `middleware/linked_data` (`rg MycoreSolrSitemap middleware/linked_data`)

## 2. Harvester: remove deprecation warning

- [ ] 2.1 Remove `warn_deprecated_linked_data_mycore_solr`, the warning message constant, and related docstring notes
      from `middleware/harvester/.../config.py`; replace `test_linked_data_mycore_solr_emits_deprecation_warning` with a
      rejection assertion; keep a test that `xml` / `regal_find` still load without mycore_solr errors — verify with
      `uv run pytest middleware/harvester/tests/unit/test_config.py -q`

## 3. Docs and examples

- [ ] 3.1 Remove commented deprecated linked_data mycore_solr blocks from `dev_environment/config_example.yaml` (and any
      other in-repo examples that still present the shim); verify `rg "sitemap_type: mycore_solr"` only hits archive /
      historical docs if at all
- [ ] 3.2 Update `docs/linked_data_to_generic.md` and `openspec/specs/sitemap-mycore-solr/design.md` to drop shim /
      soft-deprecate wording; verify they describe generic-only MyCoRe Solr

## 4. Spec sync check

- [ ] 4.1 Confirm delta specs under this change match the implemented behaviour (rejection, no warning, generic Protocol
      unchanged); verify `openspec validate --change hard-cut-linked-data-mycore-solr` (or project equivalent) succeeds
      and targeted pytest for linked_data + harvester config + generic mycore_solr still passes
