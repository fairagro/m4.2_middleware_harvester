# Tasks

## 1. Tests and fix

- [ ] 1.1 T1: a gzip `MockTransport` response decodes (fails on `main` with `DecodingError`)
- [ ] 1.2 T2: a deflate response decodes
- [ ] 1.3 T3: the returned response has no `Content-Encoding` / `Content-Length`
- [ ] 1.4 T4: a gzip body small compressed but over the limit decoded raises body-too-large
- [ ] 1.5 T5: a gzip 503 is still retried; empty body, no encoding headers
- [ ] 1.6 T6: PlabiPD harvest on the dev stack gives 2291 ARCs, from container and source

## 2. Close

- [ ] 2.1 Comment on #545 with the PR
- [ ] 2.2 Archive after merge
