# Design

## Context

See proposal.md. Placeholders are source-supplied strings an RDI writes instead of leaving a field empty (#413, #437).
Linked-data mappers check them while mapping; INSPIRE checks them in the pydantic validators of `InspireRecord`, which
the CSW `IsoParser` drives through the validation context.

## Goals / Non-Goals

**Goals:** one config object per functional class; INSPIRE placeholders configured where they are used; deployed configs
keep working; one placeholder implementation for linked-data mappers.

**Non-Goals:** see proposal.md.

## Decisions

1. **`IsoParserConfig` is a base class of the INSPIRE `Config`, not a nested block** — `IsoParser` takes one
   `IsoParserConfig` (`value_bounds`, `placeholders`) and `CSWClient` passes its whole `Config`, because a `Config` is
   an `IsoParserConfig`. A nested `inspire.parser:` block was rejected: it would move the deployed
   `inspire.value_bounds` key and need a second deprecation for no behavioural gain.
2. **The validation context stays, behind `validation_context()`** — pydantic only hands per-call settings to field
   validators through the context, so the dict remains. The function is the only way to build it, which keeps the key
   names private to `models.py` and the context's shape in one place.
3. **Lift `mapper.placeholders` to `inspire.placeholders` in `RepositoryConfig`** — same pattern as
   `linked_data.payload_type`: config load is the operator-facing surface, and the plugin never sees the legacy
   location. Only an explicitly set `mapper.placeholders` (`model_fields_set`) is lifted, so the empty default does not
   warn. Both set and different → validation error, because silently preferring one would hide an operator mistake.
4. **`mapper.placeholders` stays for linked-data mappers** — they check placeholders while mapping, so the mapper block
   is the right place there. Only the `inspire` use moves.
5. **`LinkedDataMapper.__init__(placeholders)` has no default** — config defaults live on `PlaceholderConfig`; code that
   receives placeholders MUST NOT invent its own default (harvester-configuration spec). The base `from_config` passes
   `config.placeholders`, so subclasses without other settings need no constructor.
