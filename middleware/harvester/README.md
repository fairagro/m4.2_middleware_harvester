# FAIRagro Middleware Harvester (Orchestrator)

The Middleware Harvester is a high-performance, modular orchestrator designed to bridge geo-spatial and metadata infrastructures (like INSPIRE CSW) and the FAIRagro metadata ecosystem.

## Overview

The Harvester runs as a central service that manages multiple **harvesting plugins**. It handles the orchestration loop, configuration management, and reliable transmission of Annotated Research Context (ARC) objects to the FAIRagro Middleware API.

### Key Features

- **Plugin-Based Architecture**: Easily extendable with new harvesting sources (CSW, OAI-PMH, SQL).
- **Failure Isolation**: Errors in one repository or plugin do not stop the entire harvesting run.
- **Robustness**: Comprehensive error handling and retry logic for network-bound tasks.
- **Configurable**: Centralized configuration for all plugins via YAML or Environment Variables.
- **AI-Native**: Built with Spec-Driven Development (SDD) for high maintainability.

## Configuration

The Harvester is configured using a YAML file. Values can be overridden by Environment Variables with the prefix `HARVESTER_`.

### YAML Configuration (`config.yaml`)

Example configuration:

```yaml
# Global settings
log_level: "INFO"

# OpenTelemetry settings
otel:
  log_console_spans: false
  log_level: "INFO"

# Plugin configuration
repositories:
  - rdi: "gdi-de"
    inspire:
      csw_url: "https://gdk.gdi-de.org/gdi-de/srv/eng/csw"
      max_records: 1000
      chunk_size: 50

# API Client Settings
api_client:
  api_url: "https://middleware.fairagro.net/api/v1"
  client_cert_path: "/run/secrets/client.crt"
  client_key_path: "/run/secrets/client.key"
  verify_ssl: true
```

### Full Configuration Reference

#### 1. Global Settings

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `log_level` | string | `INFO` | Console logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `repositories` | list | *(required)* | List of repository configurations. |
| `api_client` | object | *(required)* | Connection settings for the FAIRagro Middleware API (see below). |
| `otel` | object | *(required)* | OpenTelemetry configuration (see below). |

#### 2. Repository Entry (`repositories`)

Each entry in the repositories list must define the target RDI and its plugin configuration.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `rdi` | string | *(required)* | The unique RDI identifier (e.g., edaphobase). |
| `inspire` | object | `None` | Configuration for the INSPIRE plugin (must set exactly one plugin). |

#### 3. API Client (`api_client`)

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `api_url` | string | *(required)* | Base URL of the Middleware API. |
| `timeout` | float | `30.0` | Request timeout in seconds. |
| `max_concurrency` | int | `10` | Maximum parallel requests allowed to the API. |
| `verify_ssl` | bool | `true` | Whether to verify HTTPS certificates. |
| `max_retries` | int | `3` | Retries for transient HTTP errors. |
| `client_cert_path` | string | `None` | Path to client TLS certificate (PEM). |
| `client_key_path` | string | `None` | Path to client private key (PEM). |
| `ca_cert_path` | string | `None` | Path to custom CA bundle (PEM). |

#### 4. OpenTelemetry (`otel`)

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `endpoint` | string | `None` | OTLP collector endpoint URL (e.g., <http://localhost:4318>). |
| `log_level` | string | `INFO` | Logging level for OTLP export. |
| `log_console_spans` | bool | `false` | Whether to print spans to stdout for debugging. |

## Usage

### 1. From Source (Development)

Requires [uv](https://github.com/astral-sh/uv) installed.

```bash
# Install dependencies
uv sync --all-packages

# Run the harvester with a specific config
uv run python -m middleware.harvester.main -c config.yaml
```

### 2. Local Docker Image

Build and run using the provided Dockerfile:

```bash
# Build (from repository root)
docker build -f docker/Dockerfile.inspire_to_arc -t middleware-harvester:local .

# Run with local config mount
docker run --rm \
  -v $(pwd)/config.yaml:/etc/harvester/config.yaml:ro \
  middleware-harvester:local -c /etc/harvester/config.yaml
```

## CLI Options

| Option | Description |
| :--- | :--- |
| `-c, --config` | Path to the YAML configuration file. |
| `-h, --help` | Show help message and exit. |

## Documentation Links

- **[Architectural Design](../../docs/ARCHITECTURAL_DESIGN.md)**: Details on the orchestration loop and plugin contract.
- **[INSPIRE Plugin](../inspire/README.md)**: Metadata mapping and CSW settings.
- **[Specifica Workflow](../../docs/ai_workflow.md)**: Our spec-driven development approach.
