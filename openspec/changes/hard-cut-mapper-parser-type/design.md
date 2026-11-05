# Design

## Context

See proposal.md — Why. Soft-lift lives in `MapperConfig.lift_legacy_type_discriminator` and
`ParserConfig.lift_legacy_type_discriminator` (`middleware.payload` / `middleware.parsing`). Both models already use
`extra="forbid"`. In-repo YAML and closed infra overlays (#52 / #53) use type-as-key only.

## Goals / Non-Goals

**Goals:**

- Fail closed on leftover `mapper.type` / `parser.type` with an operator-facing pointer to type-as-key
- Delete soft-lift + warning strings and tests that assert warn-and-accept
- Keep nested type-as-key, shared siblings, JSON-LD ignore-for-non-JSON-LD, and the Python `.type` accessors

**Non-Goals:**

- Hard-cutting omitted-`mapper` soft-default for `inspire`
- Changing registry keys or type-child field shapes

## Decisions

1. **Explicit reject validator, not silent `extra="forbid"` alone** — Issue AC prefers a clear rejection with a pointer
   to type-as-key. Replace the before-validator lift with a before-validator that raises `ValueError` when the raw dict
   contains `type` (message mirrors today’s deprecation text, but as an error). Relying only on Pydantic’s “extra fields
   not permitted” is weaker copy. Alternative: delete the validator and depend on `extra="forbid"` — rejected for
   operator UX.

2. **Drop flat type-local field lift with the discriminator** — Legacy lift also moved root-level `resource_base_url` /
   JSON-LD fields into the type child. After hard-cut those root keys are ordinary forbidden extras; nested children
   remain the only place for them. Keep `ParserConfig._drop_jsonld_only_for_non_jsonld` for the nested ignore contract.

3. **Specs scrub only the three AC capabilities** — Narrative `mapper.type` / `parser.type` wording in other main specs
   (meaning “active registry key”) is out of scope unless a requirement still mandates deprecated lift; do not broaden
   this change into a repo-wide prose rewrite.

4. **Commit as `feat!:`** — Same pattern as other hard-cuts so Release changelog surfaces the break.

## Risks / Trade-offs

- [Out-of-repo YAML still on `type:` breaks] → Expected **BREAKING**; infra already migrated; error text names
  type-as-key.
- [Missed test still asserting warn/lift] → Grep deprecated message strings + pytest.
- [Confusion with Python `.type` property] → Keep the property; only YAML `type:` key is rejected.

## Migration Plan

1. Operators already on nested form — no action.
2. Operators still on `{ type: … }` — rewrite to type-as-key before upgrade (same mapping as #384 soft-deprecate).
3. Ship removal; no dual-read window beyond this PR.
