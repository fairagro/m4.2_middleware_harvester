# Harvester Configuration — Design

## Structure

`Config` extends `ConfigBase` (see skill:
[`.agents/skills/config-wrapper/SKILL.md`](../../../../.agents/skills/config-wrapper/SKILL.md))
and contains `api_client` and a list of `RepositoryConfig` entries. Each
`RepositoryConfig` holds shared fields (currently only `rdi`) and exactly one
optional plugin field whose Pydantic type is the plugin's own config model.

## Key Decisions

1. **Plugin type is expressed as a named optional field, not as a `type` string**
   — Each repository entry in the YAML contains shared fields alongside exactly
   one optional plugin field whose name is the plugin type (e.g. `inspire: {csw_url: ...}`).
   The named-field approach maps directly to typed Pydantic fields — full validation,
   IDE completion, and schema documentation come for free. Adding a future plugin
   is an additive change: one new optional field on `RepositoryConfig` and one entry
   in `_PLUGIN_FIELDS`.

2. **`_PLUGIN_FIELDS` class attribute as the authoritative set of mutually exclusive plugin fields**
   — `RepositoryConfig` carries a `ClassVar[frozenset[str]]` listing every optional
   plugin field by name. The `@model_validator` iterates only over that set when
   enforcing the "exactly one plugin key" invariant, rather than filtering `__dict__`
   or hardcoding non-plugin field names. This makes the intent explicit
   ("these fields are mutually exclusive") and keeps shared fields like `rdi` out of
   the validation logic entirely — adding a new shared field needs no validator change,
   and adding a new plugin field requires exactly one registration point
   (`_PLUGIN_FIELDS`) in addition to the field declaration itself.
