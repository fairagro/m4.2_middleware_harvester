## 1. Config

- [x] 1.1 Add `verify_ssl: Annotated[bool | str, Field(...)] = True` to `inspire.Config` with a clear description covering bool and CA-path forms
- [x] 1.2 Add/adjust unit tests that assert default `True`, `False`, and string path parse from dict/YAML-style input

## 2. CSW client wiring

- [x] 2.1 In `CSWClient._connect()`, construct `Authentication(verify=self._config.verify_ssl)` and pass it as `auth=` to `CatalogueServiceWeb`
- [x] 2.2 Emit a WARNING when `verify_ssl is False` before/while connecting
- [x] 2.3 Update existing connect unit tests (and add coverage) so they assert `auth.verify` for default, `False`, and CA-path cases, plus the WARNING on disable

## 3. Docs

- [x] 3.1 Document `verify_ssl` in `middleware/inspire/README.md` (default, bool disable, CA path; note it is independent of harvester API `verify_ssl`)

## 4. Validation

- [x] 4.1 Run `uv run ruff format middleware/inspire/` and `uv run pytest middleware/inspire/tests/unit/ -v` for the affected package
