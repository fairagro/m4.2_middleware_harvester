# Design

## Context

See proposal.md — Why. Shared package `fairagro-middleware-arc-validation` 14.2.0 is on PyPI (`validate_rocrate` /
`FAIRAGRO_ARC_EXPORT_IMAGE`). This repo already registers `system_local` and excludes it from pre-push. No live Docker
arc-export suite exists yet.

## Goals / Non-Goals

**Goals:**

- Smallest durable gate: pre-baked RO-Crate JSON + `system_local` + dedicated CI job
- One fixture per locked MVP family (inspire / schema.org-generic / regal)
- Readable failures via validator `cause_excerpt`

**Non-Goals:**

- Live harvest→map inside the MVP tests (refresh fixtures offline when mappings change)
- oai_pmh / phenoroam fixtures in this PR
- Editing synced Devinfra quality scripts; mocking Docker; requiring Docker on every commit

## Decisions

1. **Pre-baked RO-Crate (not map-in-test)** — Stable DataHUB-equivalent gate; mapping drift is intentional fixture
   refresh. Alternative rejected for MVP: full plugin map in CI (slower, more flaky, harder to bisect export vs map).

2. **Fixture layout** — `middleware/harvester/tests/fixtures/arc_export/<rdi>/ro-crate-metadata.json` (or equivalent
   single JSON file per RDI). Harvester owns the suite because upload/RO-Crate is the pre-API artifact boundary.

3. **Dependency placement** — Add `fairagro-middleware-arc-validation>=14.2.0` to `harvester` (dev or main deps as
   needed for test import; prefer dev dependency if the package is test-only).

4. **Markers** — Primary `@pytest.mark.system_local`. Optional `requires_docker` only if it helps selection; do not
   invent a second gate that fights pre-push. Skip clearly when Docker is missing if a job accidentally collects the
   tests without Docker (fail closed in the dedicated CI job).

5. **CI** — New Feature-PR job (not folded into `reusable-code-quality`): checkout, `uv sync`, pin
   `ghcr.io/nfdi4plants/arc-export@sha256:…`, build a thin local tag that symlinks `/usr/local/bin/arc-export` →
   `/arc-export` (current image has no `arc-export` on `PATH`; package invokes the bare command), set
   `FAIRAGRO_ARC_EXPORT_IMAGE` to that tag, then `uv run pytest -m system_local`. Runner `ubuntu-latest` provides
   Docker. Skip when Feature `code` path filter is false.

6. **Producing initial fixtures** — Offline once: map a minimal representative record per family (dev_environment / unit
   fixtures / small hand-built ARC via arctrl) → serialize RO-Crate JSON → commit. Prefer minimal valid crates that
   already pass `arc-export` locally before push.

7. **Docs** — Short section in harvester-facing docs or `docs/` (product-local, not synced `docs/quality.md`): Docker
   requirement, how to run `pytest -m system_local`, how to add a fixture after DataHUB failure.

8. **LFS** — Not for MVP unless a fixture exceeds a comfortable git blob size; revisit then.

## Risks / Trade-offs

- **[Risk] CI image pull / GHCR rate limits** → Pin digest; cache where Actions allows; document override env.
- **[Risk] Stale fixtures hide mapper regressions** → Doc requires adding a fixture when DataHUB fails; optional later
  follow-up to generate crates from source in a slower job.
- **[Risk] arc-export upstream breaks good fixtures** → Digest pin freezes behaviour; bump deliberately with suite
  green.
- **[Risk] Package invokes `arc-export` but image only ships `/arc-export`** → PATH symlink wrapper image in tests/CI;
  follow-up to fix `fairagro-middleware-arc-validation` / coordinate with nfdi4plants image layout.

## Migration Plan

1. Land dependency + fixtures + tests + CI job + doc in one PR.
2. Operators run `system_local` locally only with Docker.
3. Follow-up issues for additional RDIs (oai_pmh, phenoroam) as they become “active”.
