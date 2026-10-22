# Tasks

## 1. Config + client enforcement

- [ ] 1.1 Add `NiceHttpClientConfig.max_response_body_bytes` (default `33554432`, `ge=1`) and verify model default /
      validation via unit test
- [ ] 1.2 Implement Content-Length pre-check + streamed body read with limit in `retry_get_with_client` (and robots.txt
      fetch path); raise a clear non-retryable body-too-large error; verify unit tests for oversized Content-Length,
      oversized streamed body, and exact-limit success
- [ ] 1.3 Confirm body-too-large is not retried as transient 5xx/429; verify with a unit test that only one attempt runs

## 2. Harvest failure mapping

- [ ] 2.1 Trace at least one plugin/`get_with_policy` caller and confirm oversized bodies become record- or
      repository-level harvest failures without crashing the process (extend an existing test or add a focused one)

## 3. Specs already in this change

- [ ] 3.1 Keep delta specs aligned with the implemented error behaviour; verify
      `openspec validate cap-http-response-body-size` succeeds
