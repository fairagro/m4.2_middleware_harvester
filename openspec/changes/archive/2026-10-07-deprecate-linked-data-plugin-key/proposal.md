# Proposal

## Why

Equivalent harvest paths now prefer `generic:` + nested `protocol` / sibling `parser` / `mapper`. The `linked_data:`
plugin key remains a temporary shim, but operators get no signal when the whole plugin key is still in use (only some
sitemap types warn). Soft-deprecating the key and flipping in-repo examples removes the “still recommended” impression
before a later hard cut (#296 phase 2).

## What Changes

- Emit a clear `logger.warning` once per repository config load when `linked_data:` is set, pointing operators at
  `generic:` + Protocol/Parser (and docs such as `docs/linked_data_to_generic.md`). Shim behaviour unchanged (no hard
  fail).
- Migrate in-repo Publisso / Regal examples from `linked_data` to `generic` + `parser.type: jsonld` with
  `allowed_context_url` (`dev_environment/config.all-rdis.yaml`, `helm/harvester/values.yaml` example).
- Update OpenSpec so coexistence is explicitly **deprecated** (still supported until a follow-up hard-cut issue).
- **Non-goals:** Removing the `linked_data` plugin key, orchestrator branch, or Sitemap/Dataset shims (**BREAKING** —
  deferred). Out-of-repo cluster overlays. Closing #395/#396 hard-cuts in this change.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvester-configuration`: Require a deprecation warning when a repository sets the `linked_data` plugin key.
- `linked-data-harvesting`: Mark plugin-key coexistence as deprecated (still valid; warn at config load); keep
  unmigrated configs working until a later hard cut.

## Impact

- `middleware/harvester` `RepositoryConfig` validators + unit tests
- In-repo YAML/Helm examples; `docs/linked_data_to_generic.md` (note that examples prefer `generic`)
- Follow-up hard-cut issue remains #296 phase 2 (or a linked issue) after operators migrate
