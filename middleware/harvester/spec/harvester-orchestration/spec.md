# Harvester Orchestration

The central harvester acts as an orchestrator that loads a unified configuration, executes multiple pluggable `xxx_to_arc` components, and publishes the resulting ARCs to the FAIRagro Middleware API.

## Requirements

- [ ] Load a centralized configuration that inherits from `ConfigBase`.
- [ ] Parse a `repositories` list from the configuration, where each entry contains shared fields (e.g. `rdi`) and exactly one optional plugin field whose name is the plugin type (e.g. `inspire`) and whose value is the plugin-specific configuration object.
- [ ] Parse `api_client` settings globally within the harvester configuration, rather than within localized plugins.
- [ ] Instantiate and invoke the appropriate `xxx_to_arc` plugin by looking up the plugin type key in `_PLUGIN_CLASSES`, instantiating the corresponding `Plugin` subclass with the plugin-specific config, and calling `.run()` and `.get_expected_datasets()` via the `Plugin` interface.
- [ ] `Plugin.run()` is an `async` generator method (declared with `async def`) returning `AsyncGenerator[str | HarvesterError, None]`.
- [ ] `Plugin.get_expected_datasets()` is an `async` method returning `int | None`.
- [ ] The `Plugin` base class defines no `__init__` method; each concrete subclass defines its own constructor with its own strongly-typed config parameter.
- [ ] Consume the output of each plugin via an `AsyncGenerator[str | HarvesterError, None]` that yields either serialized ARC JSON strings or `HarvesterError` instances for record-level failures.
- [ ] Upload the yielded ARCs to the target Remote Data Infrastructure (RDI) using the configured `api_client`.
