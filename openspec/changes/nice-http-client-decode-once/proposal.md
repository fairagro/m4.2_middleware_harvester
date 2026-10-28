# Proposal

## Why

#545: since #521 (65a224e, response body cap), `NiceHttpClient._get_with_body_limit` collects the body with
`aiter_bytes()`, which is already decoded, and wraps it in a new `httpx.Response` that still carries
`Content-Encoding: gzip`. httpx decodes it a second time and raises `httpx.DecodingError` ("Error -3 while decompressing
data: incorrect header check"). raw.githubusercontent.com always gzips, so PlabiPD discovery fails and none of its
genomes are harvested on `main`. Any other gzip- or deflate-serving source is affected the same way.

## What Changes

- A compressed response is decoded exactly once; the returned response carries no `Content-Encoding` and no
  `Content-Length` header (also on the empty-body 429/5xx path).
- The body cap counts decoded bytes. The early `Content-Length` check is unchanged (compressed size ≤ decoded size).
- **Non-goals:** brotli/zstd (libraries not installed); per-RDI checks of other gzip sources; #546.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `nice-http-client`: compressed responses are decoded once and the body cap applies to the decoded size.

## Impact

- `middleware/contracts/src/middleware/contracts/nice_http_client.py` and its tests
