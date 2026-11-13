# ARC export fixture gate (`system_local`)

Representative RO-Crate fixtures are validated with the same DataHUB check (`arc-export`) via
`fairagro-middleware-arc-validation`, so mapping regressions that break export are caught in client CI before upload.

## Requirements

- Docker (socket access to pull/run images)
- Dev dependency: `fairagro-middleware-arc-validation` (installed with `uv sync --dev --all-packages`)

## Run locally

```bash
uv sync --dev --all-packages
uv run pytest -m system_local middleware/harvester/tests/system_local -v
```

Default commit-stage / pre-push pytest **excludes** `system_local` (no Docker required on every push).

### Image / PATH note

`ghcr.io/nfdi4plants/arc-export` ships the binary as `/arc-export`, while the validation package invokes the command
`arc-export`. The test suite builds a thin local tag (`fairagro-arc-export-path:ci`) that symlinks
`/usr/local/bin/arc-export` → `/arc-export`, unless you already set `FAIRAGRO_ARC_EXPORT_IMAGE`.

Base image digest SoT: `middleware/harvester/tests/system_local/arc-export-base.digest` (CI and local wrapper build both
read it). Override the final image anytime:

```bash
export FAIRAGRO_ARC_EXPORT_IMAGE='ghcr.io/nfdi4plants/arc-export@sha256:…'  # only if PATH is fixed
# or any image where `arc-export` is on PATH
```

## Fixture layout

```text
middleware/harvester/tests/fixtures/arc_export/<rdi>/ro-crate-metadata.json          # optional smoke
middleware/harvester/tests/fixtures/arc_export/<rdi>/<case-id>/ro-crate-metadata.json # real-data cases
```

`system_local` discovers **every** leaf directory under `arc_export/` that contains `ro-crate-metadata.json` (smoke and
nested cases). The first path segment is the RDI id.

**Active RDI inventory** for real-data suites: enabled repositories in `dev_environment/config.all-rdis.yaml` (OpenAgrar
live MODS suite landed in #614). Technology family is secondary — sibling RDIs can diverge even when they share a
mapper.

Minimal MVP smoke crates may remain for `bonares` / `publisso` alongside real-data sets. `openagrar` is nested real-data
only (smoke removed in #614).

### Real-data suites (status)

| RDI                     | Status                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| bonares                 | Real-data cases under `fixtures/arc_export/bonares/<uuid>/` (+ smoke at folder root); see that folder’s `README.md`             |
| edal                    | Real-data cases under `fixtures/arc_export/edal/<doi-slug>/`; see that folder’s `README.md` (#610)                              |
| publisso                | Real-data cases under `fixtures/arc_export/publisso/<frl-slug>/` (+ smoke at folder root); see that folder’s `README.md` (#611) |
| sradi                   | Deferred — #612                                                                                                                 |
| plabipd                 | Real-data cases under `fixtures/arc_export/plabipd/<composite-id>/`; see that folder’s `README.md` (#613)                       |
| openagrar (live / MODS) | Real-data cases under `fixtures/arc_export/openagrar/<mods-id>/` (no root smoke); see that folder’s `README.md` (#614)          |
| phenoroam               | Real-data cases under `fixtures/arc_export/phenoroam/<uuid>/`; see that folder’s `README.md` (#615)                             |
| openagrar-fixture       | Local fixture-server stand-in only; does not satisfy the OpenAgrar live suite (#614)                                            |

## Generate a real-data fixture

1. Curate one or more **real** source records for the RDI (live endpoint or archived harvest input).
2. Map them through the **real client path** for that RDI (same plugin + mapper config operators use — e.g. inspire
   plugin + `inspire_general` for bonares).
3. Write `ro-crate-metadata.json` under `tests/fixtures/arc_export/<rdi>/<case-id>/`.
4. Document which input features the case covers (folder `README.md` and/or this doc).
5. Run `uv run pytest -m system_local middleware/harvester/tests/system_local -v`.

Prefer failing-test-first when a production / DataHUB `arc-export` gap appears: add the failing crate, fix the mapper,
re-run until green.

### Git LFS and redaction

- Use **Git LFS** when a crate (or the suite) is large enough to hurt clone/CI (rough guide: multi‑MB JSON). Prefer
  small curated sets (single-digit files per RDI) over full harvest dumps.
- **Redact** personal emails / phone numbers in committed crates when they are not required to reproduce the
  `arc-export` failure mode; note redactions next to the case coverage list. Do not invent synthetic contacts to “fix”
  redaction — omit or replace with obvious placeholders only when needed for privacy.

## Add a fixture after a DataHUB / production failure

1. Capture the failing RO-Crate (or regenerate from the source record that failed `arc-export`).
2. Add it under `tests/fixtures/arc_export/<rdi>/` (new case dir, or replace the representative if appropriate).
3. Run `uv run pytest -m system_local middleware/harvester/tests/system_local -v` — expect **fail** with a readable
   `cause_excerpt`.
4. Fix the mapper / payload; re-run until green; commit fixture + fix together when possible.
