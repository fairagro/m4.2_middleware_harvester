# FAIRagro Middleware Harvester

This repository contains the Middleware Harvester, a core component of the FAIRagro advanced
middleware architecture. It acts as an orchestrator that runs specialized harvesting plugins
(like the INSPIRE-to-ARC converter). It enables Research Data Infrastructure (RDI) providers to
harvest metadata from standardized sources (like CSW), transform them into standardized Annotated
Research Context (ARC) objects, and transmit them to the central FAIRagro Middleware API.

## 📁 Repository Structure

| Path | Description |
| :--- | :--- |
| [`middleware/harvester/`](middleware/harvester/README.md) | Source code of the central orchestrator and plugin contract. |
| [`middleware/inspire/`](middleware/inspire/README.md) | Source code of the INSPIRE-to-ARC harvester plugin. |
| `docs/` | Architectural design, mapping specifications, and AI workflow. |
| `openspec/` | OpenSpec specs (current behaviour) and in-flight changes. |
| `dev_environment/` | Docker-based local development setup (Mock API, Harvester). |
| `scripts/` | Tooling for quality checks, environment setup, and Git LFS. |
| `docker/` | Dockerfiles and container structure tests. |

## 🌟 Quick Start (Full Local Demo)

For the best out-of-the-box experience, you can run a complete local demonstration. This setup starts a local Mock Middleware API and the Harvester to process and save results locally:

```bash
# Start the full demo stack (requires Docker)
./dev_environment/start.sh
```

Note: Generated ARCs will be saved to `dev_environment/demo_output/`.

## 🚀 Getting Started (Development)

The preferred method for working with this repository is using a **Dev Container** (VS Code or Cursor).

- Config: [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) — see [`.devcontainer/README.md`](.devcontainer/README.md) for setup notes

### 1. Prerequisites (for manual setups only)

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Dependency Management & Workspace Orchestration)
- Docker & Docker Compose
- Git LFS (installed via `./scripts/setup-git-lfs.sh`)

### 2. Environment Setup

Clone the repository and install all workspace dependencies:

```bash
uv sync --all-packages
```

### 3. Start Local Development Environment

The `dev_environment` folder provides a full stack including a Mock API. Please refer to the [Development Environment README](dev_environment/README.md) for detailed instructions.

## 🔧 Component Documentation

Detailed information on how to use, configure, and deploy the specific components can be found in their respective subdirectories:

- **[Harvester Orchestrator README](middleware/harvester/README.md)**: Configuration (YAML/Env), CLI options, and orchestration loop.
- **[INSPIRE Plugin README](middleware/inspire/README.md)**: Metadata mapping rules and CSW connection settings.
- **[Architectural Design](openspec/specs/harvester-orchestration/design.md)**: Deep dive into the concurrency model and data flow.
- **[INSPIRE Mapping Spec](docs/inspire_mapping.md)**: The rules for transforming INSPIRE/ISO19139 metadata into ARC objects.

## 🤖 AI-Native Development

This project uses **[OpenSpec](https://github.com/Fission-AI/OpenSpec)** for spec-driven
development. Current behaviour lives in `openspec/specs/`; in-flight work uses
`openspec/changes/` via `/opsx-propose` → `/opsx-apply` → `/opsx-archive`.

AI agents use these specs along with `AGENTS.md` and `.agents/skills/` for high-context assistance.

- See **[AI Agent Workflow](docs/ai_workflow.md)** for details on how to use agents effectively in this project.

## 🧪 Quality Standards

We maintain high code quality through automated checks:

```bash
# Run all quality checks (Ruff, Mypy, Pylint, Bandit)
./scripts/quality-check.sh

# Run unit and integration tests
uv run pytest middleware/
```

Maintained by: **FAIRagro Middleware Team** | License: [LICENSE](LICENSE)
