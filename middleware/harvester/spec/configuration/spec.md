# Harvester Configuration

Defines the structure of the harvester configuration file. The configuration
is validated at startup via Pydantic; an invalid config aborts the process
before any harvesting begins.

All configuration classes follow the `ConfigWrapper / ConfigBase` pattern
(see skill: [`.agents/skills/config-wrapper/SKILL.md`](../../../../.agents/skills/config-wrapper/SKILL.md)):
YAML file as source, individual values overridable via environment variables
or `/run/secrets/` files, Pydantic `BaseModel` with fully typed fields (no
`dict[str, Any]` or `Any`), loaded via `Config.from_config_wrapper(wrapper)`.

## Requirements

- [ ] The configuration must contain exactly one `api_client` section.
- [ ] The configuration must contain a non-empty `repositories` list.
- [ ] Each repository entry must contain a shared `rdi` field (string, required).
- [ ] Each repository entry must contain exactly one plugin field (e.g. `inspire`); zero or two or more plugin fields are rejected with a validation error.
- [ ] Plugin field types are statically typed Pydantic models; no `dict[str, Any]` is used for plugin config.

## Edge Cases

Repository entry with no plugin field → `ValidationError` at startup, process aborts.

Repository entry with two plugin fields set → `ValidationError` at startup, process aborts.

Repository entry with an unrecognised key → Pydantic ignores extra fields by default; no silent data loss because `_PLUGIN_FIELDS` drives dispatch, not raw dict keys.
