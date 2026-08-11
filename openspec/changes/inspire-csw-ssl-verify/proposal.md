## Why

Some CSW endpoints use self-signed or privately issued TLS certificates. Today the INSPIRE plugin always lets OWSLib verify certificates (`verify=True`), so harvests against those endpoints fail at connect time with no config escape hatch. Operators need a way to disable verification or point at a custom CA bundle.

## What Changes

- Add an `inspire.Config` field `verify_ssl` (default `True`) that maps to OWSLib `Authentication(verify=...)`.
- Forward that value from `CSWClient._connect()` when constructing `CatalogueServiceWeb`.
- Support `bool` (enable/disable) and `str` (path to a CA bundle), matching OWSLib’s `Authentication.verify` contract.
- Document the field for operators; log a warning when verification is disabled.

## Non-Goals

- Changing Middleware API upload SSL settings (`harvester` `verify_ssl` remains separate).
- Client-certificate (mTLS) authentication via OWSLib `Authentication.cert`.
- Migrating CSW HTTP onto `NiceHttpClient` (OWSLib keeps its own `requests` stack).

## Capabilities

### New Capabilities

- `csw-ssl-verify`: Configurable TLS certificate verification for INSPIRE CSW / OWSLib connections.

### Modified Capabilities

- (none)

## Impact

- **Affected domains**: new `openspec/specs/csw-ssl-verify/`; related pattern in `csw-retry` (how connection params are forwarded to `CatalogueServiceWeb`).
- **Code**: `middleware/inspire/src/middleware/inspire/config.py`, `csw_client.py`; unit tests under `middleware/inspire/tests/unit/`.
- **Config**: optional `verify_ssl` under INSPIRE plugin YAML (default preserves current behaviour).
- **Dependencies**: none new — uses existing OWSLib `Authentication`.
