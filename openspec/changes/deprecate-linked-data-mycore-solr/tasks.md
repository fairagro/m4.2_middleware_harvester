# Tasks

## 1. Prerequisite / branch base

- [ ] 1.1 Ensure this branch includes the thin linked_data MyCoRe Solr shim from #293 / PR #385 (rebase onto or merge
      `build/issue-293-mycore-solr-generic-protocol` / merged main) and verify
      `middleware/linked_data/.../sitemap/mycore_solr.py` delegates to `MycoreSolrProtocol`

## 2. Deprecation warning

- [ ] 2.1 Add a repository-config (or linked_data Config) validator that emits `logger.warning` when
      `linked_data.sitemap_type == mycore_solr`, using the agreed copy pointing at `generic.protocol.mycore_solr` (+
      sibling parser/mapper); verify a new unit test with `caplog` asserts the warning and that validation still
      succeeds
- [ ] 2.2 Confirm other `sitemap_type` values (`xml`, `regal_find`) do not emit this warning; verify via unit test
      assertions

## 3. Docs and examples

- [ ] 3.1 Update `dev_environment/config_example.yaml` so the OpenAgrar / MyCoRe example uses nested
      `generic.protocol.mycore_solr` (keep robots note); verify the file no longer presents `linked_data` +
      `mycore_solr` as the preferred form
- [ ] 3.2 Sync field descriptions / comments on linked_data `sitemap_type` / MyCoRe docs to mark the linked_data path
      deprecated; verify wording matches the warning

## 4. Follow-up hard cut

- [ ] 4.1 Open a GitHub follow-up Task to remove `SitemapType.mycore_solr` and the linked_data shim after operators
      migrate (link #387 / #383-style); verify the issue URL is referenced from the PR or this change's notes

## 5. Integration check

- [ ] 5.1 Run targeted unit tests for harvester/linked_data config deprecation and MyCoRe shim (`uv run pytest` on the
      touched test modules) and verify they pass
