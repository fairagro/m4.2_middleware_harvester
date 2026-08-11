## Context

`CSWClient._connect()` constructs `owslib.catalogue.csw2.CatalogueServiceWeb` with `timeout` and `headers` only. OWSLib already supports TLS control via `auth=Authentication(verify=...)`, where `verify` is `bool | str` (system CA / disable / CA bundle path). That value is stored on the CSW instance and passed into every `openURL` / `http_post` call. See proposal.md for motivation. Related forwarding pattern: `openspec/specs/csw-retry/` (`user_agent` → `headers`).

## Goals / Non-Goals

**Goals:**

- Expose a single flat `inspire.Config` field that maps 1:1 onto OWSLib `Authentication.verify`.
- Keep default behaviour identical to today (`True`).
- Make disabling verification visible in logs.

**Non-Goals:**

- Sharing this field with harvester API-client `verify_ssl` (different HTTP stack, different config tree).
- mTLS client certificates (`Authentication.cert`).
- Replacing OWSLib’s HTTP layer with `NiceHttpClient`.

## Decisions

1. **Field name `verify_ssl` (not `ssl_verify` / `verify`)**
   — Matches the existing harvester API-client YAML key operators already know from `middleware/harvester/README.md` and Helm values. Same semantics (TLS peer verification), different config subtree (`plugin` vs top-level API client). Alternatives considered: `ssl_verify` (closer to requests kwargs) and nesting under an `auth:` object — rejected to keep flat INSPIRE fields consistent with `timeout` / `user_agent` / retry knobs.

2. **Type `bool | str`, default `True` — mirror OWSLib exactly**
   — OWSLib’s `Authentication.verify` already accepts bool or CA-bundle path. Supporting the string form gives operators a safer alternative to `False` for privately issued certs. Alternatives considered: bool-only (simpler YAML, but forces full disable when a CA path would suffice) and separate `ca_bundle` + `verify_ssl` fields (more verbose, easy to misconfigure when both are set).

3. **Pass via `Authentication(verify=...)` at `CatalogueServiceWeb` construction**
   — Same lifetime as `user_agent` headers: one injection covers GetCapabilities and all later GetRecords calls. Do not patch `requests` globals or set `PYTHONHTTPSVERIFY`. Alternatives considered: monkeypatching `openURL` — fragile across OWSLib versions.

4. **Warn only when `verify_ssl is False`; not when using a CA path**
   — Disabling verification is a security downgrade that operators must notice. A custom CA path still verifies the peer and does not need a warning. Alternatives considered: warning on any non-default — too noisy for legitimate private-CA deployments.

5. **No eager filesystem validation of CA path in pydantic**
   — OWSLib already `os.stat`s the path when `Authentication.verify` is set and fails at connect time. Duplicating that in Config would couple config load to the runtime filesystem (awkward for ConfigWrapper / secret mounts that appear later). Invalid paths surface as connection errors wrapped by existing `CswConnectionError` handling.

## Risks / Trade-offs

- **[Risk] Operators leave `verify_ssl: false` in production** → Mitigation: WARNING log on every connect; document preferred CA-path form in README.
- **[Risk] Name collision confusion with harvester `verify_ssl`** → Mitigation: document clearly that INSPIRE `verify_ssl` is under the plugin config block and only affects CSW/OWSLib.
- **[Trade-off] No mTLS in this change** → Acceptable; can extend `Authentication(cert=...)` later without changing the `verify_ssl` contract.

## Migration Plan

- Additive config field with default `True` — no migration required for existing YAML.
- Rollback: omit the field or remove the code path; behaviour returns to always-verify.
