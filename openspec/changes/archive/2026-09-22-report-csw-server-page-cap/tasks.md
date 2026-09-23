# Tasks — Report the CSW server's advertised page-size cap

## 1. Implementation

- [x] 1.1 Add `capabilities.py` with `advertised_max_records`, `warn_if_server_caps_page_size` and a
      tolerant `_first_int`. A new module rather than a `CSWClient` method because `csw_client.py`
      was at 999 of its 1000-line pylint ceiling — see design decisions 4 and 5.
- [x] 1.2 Call `warn_if_server_caps_page_size` from `_connect` after the `CatalogueServiceWeb` is
      constructed, guarded so a missing / reshaped constraint cannot raise during connect.
- [x] 1.3 Move the existing service-title extraction into `capabilities.describe_service`, which
      keeps the capability readers together and frees the line the call needed.

## 2. Tests

- [x] 2.1 Warning emitted when the advertised cap is below `chunk_size`, naming both values.
- [x] 2.2 No warning when the cap is at or above `chunk_size`.
- [x] 2.3 No warning and no exception when the constraint is absent, non-numeric, or non-positive.
- [x] 2.4 No warning and no exception when `constraints` itself is missing or not a mapping.
- [x] 2.5 Confirm the tests are non-vacuous: inverting the comparison fails 3, and dropping the
      positivity guard in `_first_int` fails 3 others.
- [x] 2.6 Cover `describe_service` too, since its behaviour moved modules.

## 3. Quality gate

- [x] 3.1 `uv run pytest middleware/ -q` — 454 passed
- [x] 3.2 `source .devcontainer/product.env` then `uv run mypy middleware/ --config-file mypy.ini`
      (88 files, tests included — CI's invocation) — Success
- [x] 3.3 `uv run pre-commit run --all-files` — ruff, bandit and pylint pass. The mypy hook and
      markdownlint fail identically on a clean `origin/main` tree (verified by stashing), so both are
      pre-existing host-only noise, not this change: the hook does not source `MYPYPATH` from
      `.devcontainer/product.env` (cf. #299), and markdownlint's `**/*.md` glob reaches into `.git/`
      where a remote branch name ends in `.md`.
- [x] 3.4 `openspec validate --specs` (28 passed) and `openspec validate report-csw-server-page-cap`
- [x] 3.5 `csw_client.py` is at 998 lines, one below where it started

## 4. Archive

- [x] 4.1 `openspec archive report-csw-server-page-cap`
- [x] 4.2 Confirm the requirement landed in `openspec/specs/csw-harvesting/spec.md`
