# Configuration Design

## Key Decisions

— Using the `ConfigWrapper` and `Pydantic` models for the config parser over untyped `dict` loads.
Strongly typing configuration flags makes configuration a secure schema. Instead of validating at the usage site (like inside the loop), the app fails immediately on startup if an invalid config file is run.

— No environment variable bindings for passwords natively.
Security is deferred to `middleware.shared.config.config_base` or injected at runtime. By avoiding `os.environ` in `middleware/inspire_to_arc/config.py`, the core codebase abstracts away whether it's running in Docker or natively.

— Treating `ApiClientConfig` as passed-through block.
The `Config` parses an `api_client` map, but leaves its core interpretation to `middleware.api_client.config`. Harvester logic knows nothing of auth or retry delays directly.
