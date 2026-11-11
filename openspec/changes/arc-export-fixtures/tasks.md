# Tasks

## 1. Dependency and docs scaffolding

- [ ] 1.1 Add `fairagro-middleware-arc-validation>=14.2.0` to the harvester (dev) dependency set and lockfile; verify
      `uv sync --dev --all-packages` succeeds and
      `uv run python -c 'from middleware.arc_validation import validate_rocrate'` imports
- [ ] 1.2 Add a short product-local doc (or README section) covering Docker requirement, how to run
      `pytest -m system_local`, and how to add a fixture after a DataHUB/`arc-export` failure; verify the doc mentions
      all three

## 2. Fixtures and system_local tests

- [ ] 2.1 Commit one minimal pre-baked RO-Crate JSON under `middleware/harvester/tests/fixtures/arc_export/<rdi>/` for
      each MVP family (inspire, schema.org/generic, regal); verify each file exists and is valid JSON
- [ ] 2.2 Add `system_local` pytest that loads each fixture, calls `validate_rocrate`, asserts `.ok`, and on failure
      surfaces `cause_excerpt`; verify tests are collected with `-m system_local` and are excluded by
      `-m "not system_local"`
- [ ] 2.3 With Docker available, run `uv run pytest -m system_local` on the new suite and verify all three fixtures pass
      (or fix crates until they do)

## 3. CI job

- [ ] 3.1 Add a Feature-PR workflow job that runs the `system_local` arc-export suite with Docker and a pinned
      `FAIRAGRO_ARC_EXPORT_IMAGE` digest (skip when no relevant paths changed if matching existing filters); verify the
      workflow YAML references `system_local` and the image env var

## 4. Validate

- [ ] 4.1 Run `openspec validate arc-export-fixtures` and focused ruff/format on touched Python; verify validate and
      checks succeed
