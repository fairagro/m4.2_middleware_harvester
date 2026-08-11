# Harvester Orchestration — Design

## Architecture

The project consists of a core orchestrator module (`middleware/harvester`) and several plugin modules (like `middleware/inspire`). The orchestrator translates unified configuration into specific plugin invocations, completely separating the metadata extraction logic from the publishing logic.

## Key Decisions

1. **Decoupling data extraction into separate plugins**
   — Because different sources (e.g., CSW vs. Schema.org) employ fundamentally different fetching protocols and metadata standards, the specific fetch and map responsibilities stay inside isolated `xxx_to_arc` modules.

2. **Using an `AsyncGenerator` yielding `HarvestedArc` as the plugin interface**
   — Plugins yield `HarvestedArc` (serialized ARC JSON plus study/assay counts
   and optional source URL) asynchronously. This keeps arctrl objects inside
   the plugin, lets the orchestrator upload concurrently while the plugin
   fetches the next record, and avoids re-parsing RO-Crate JSON for composition
   counts.

3. **Moving `api_client` configuration to the Harvester core**
   — Individual plugins should not know about or be responsible for uploading data to the FAIRagro Middleware API. By lifting `api_client` into the central harvester configuration, we ensure single-point authentication, unified connection handling, and centralized error logging for all uploads.

4. **Plugin dispatch via a static registry dict (`PLUGIN_FACTORIES`)**
   — `orchestrator.py` holds a module-level dict mapping plugin type names to
   their `Plugin` subclasses. The orchestration loop looks up the class by
   `repo.plugin_type`, instantiates it with `repo.plugin_config`, and calls
   `.run()` and `.get_expected_datasets()` via the `Plugin` interface. This
   avoids an `if/elif` chain that would grow with every new plugin. Adding a
   new plugin requires one import and one dict entry in `PLUGIN_FACTORIES`;
   the orchestrator loop itself needs no changes.

5. **`Plugin` is a structural Protocol (do not inherit); `run` is an async generator**
   — Each concrete plugin defines its own `__init__(self, config: <PluginConfig>)`
   with a precise type for its own config. `PLUGIN_FACTORIES` is typed as
   `Callable[..., Plugin]` and relies on structural typing. Implementations
   declare `async def run` with `yield` (OpenSpec). The Protocol stub must use
   a plain `def run(...) -> AsyncGenerator[...]`: under mypy, marking the Protocol
   method `async def` would type `plugin.run()` as a coroutine returning an
   async generator, breaking `async for` at the call site. Do not subclass
   `Plugin` to avoid a false sync/async override conflict in pylint.
