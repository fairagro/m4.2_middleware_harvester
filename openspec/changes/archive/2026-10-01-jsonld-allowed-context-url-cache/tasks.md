# Tasks

## 1. ParserConfig + shared context loader

- [x] 1.1 Add optional `allowed_context_url` to `ParserConfig` and unit-test model validation (accept http(s) URL /
      unset). Verify: `uv run pytest middleware/parsing/tests/unit/ -k allowed_context -q` (or new test module).
- [x] 1.2 Implement process-lifetime context document cache + polite HTTP fetch-on-miss helper under
      `middleware.parsing`, including transitive `@import` population into the same cache. Verify: unit tests with a
      fake HTTP client proving second resolve issues zero GETs and import URLs are cached.
- [x] 1.3 Wire an rdflib/parse path that serves contexts only from the cache (no uncached default remote load). Verify:
      test that parse after prefetch does not call HTTP for the context URL.

## 2. JsonLdParser + HtmlJsonLdParser

- [x] 2.1 Update `JsonLdParser`: remove Schema.org `@vocab` stub; enforce unset vs `allowed_context_url` match; resolve
      via shared loader; require non-null client on cache miss. Verify: extend
      `middleware/parsing/tests/unit/test_jsonld_parser.py`.
- [x] 2.2 Update `HtmlJsonLdParser`: drop hard-coded Schema.org allowlist gate; apply the same `allowed_context_url` +
      loader policy before/during parse. Verify: extend `middleware/parsing/tests/unit/test_html_jsonld_parser.py`.
- [x] 2.3 Adjust any `jsonld_validation` call sites so harvest parse no longer depends on the module Schema.org
      allowlist for accept/reject of remote IRIs (mapper-only use may remain). Verify: affected unit tests green.

## 3. Operator examples + docs

- [x] 3.1 Set `parser.allowed_context_url` on in-repo Schema.org examples that use remote Schema.org IRIs
      (`dev_environment` / Helm as needed for this breaking config). Verify: configs still `Config.model_validate` /
      repository load.
- [x] 3.2 Update `docs/linked_data_to_generic.md` (and example comments) to describe `allowed_context_url` and that
      Regal/Publisso can move to `generic`+`jsonld` once this ships (migration itself still follow-up). Verify: doc
      review in PR.

## 4. Quality

- [x] 4.1 Run focused parsing tests plus format/lint on touched paths (`uv run pytest middleware/parsing/tests/unit -q`,
      `uv run ruff format` / `ruff check` on edited files). Verify: commands exit 0.
