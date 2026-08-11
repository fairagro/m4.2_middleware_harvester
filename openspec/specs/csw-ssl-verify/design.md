# CSW SSL Verify — Design

## Architecture

`CSWClient._connect()` constructs `CatalogueServiceWeb` with
`auth=Authentication(verify=config.verify_ssl)`. OWSLib stores that
`Authentication` on the client and passes `verify` into every subsequent
`openURL` / `http_post` call for the client lifetime.

```text
inspire.Config.verify_ssl  (bool | str, default True)
        │
        ▼
CSWClient._connect()
        │
        ├─ WARNING if verify_ssl is False
        └─ CatalogueServiceWeb(..., auth=Authentication(verify=...))
                │
                └─ all CSW HTTP (GetCapabilities, GetRecords, …)
```

## Key Decisions

1. **Field name `verify_ssl` (not `ssl_verify` / `verify`)**
   — Matches the existing harvester API-client YAML key. Same semantics (TLS peer
   verification), different config subtree (`plugin` vs top-level API client).
   Alternatives considered: `ssl_verify`; nesting under an `auth:` object —
   rejected to keep flat INSPIRE fields consistent with `timeout` / `user_agent`.

2. **Type `bool | str`, default `True` — mirror OWSLib exactly**
   — OWSLib’s `Authentication.verify` already accepts bool or CA-bundle path.
   String form is a zero-cost passthrough and a safer alternative to `False` for
   privately issued certs.

3. **Pass via `Authentication(verify=...)` at `CatalogueServiceWeb` construction**
   — Same lifetime as `user_agent` headers: one injection covers GetCapabilities
   and all later GetRecords calls.

4. **Warn only when `verify_ssl is False`; not when using a CA path**
   — Disabling verification is a security downgrade. A custom CA path still
   verifies the peer.

5. **No eager filesystem validation of CA path in pydantic**
   — OWSLib already `os.stat`s the path when `Authentication.verify` is set and
   fails at connect time. Invalid paths surface as `CswConnectionError`.

6. **Coerce boolean-like strings before accepting a CA path**
   — Under `bool | str`, Pydantic keeps quoted `"false"` / `"true"` as `str`.
   A `mode="before"` validator maps common truthy/falsy strings to `bool` so
   YAML quotes and env-var overrides disable verification instead of becoming
   bogus CA paths.
