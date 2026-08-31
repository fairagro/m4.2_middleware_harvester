# AGENTS.md - Instructions for AI Assistants

This file contains critical context about the FAIRagro Middleware Harvester project for AI assistants (GitHub Copilot, Google Antigravity, Claude, etc.).

## 📋 Tech Stack

| Component | Version | Details |
| --------- | ------- | ------- |
| Python | 3.12+ | Primary language |
| CSW | 2.0.2 | Source protocol (Catalogue Service for the Web) |
| Docker | Latest | Containerization |
| uv | Latest | Python package manager |
| arctrl | Latest | ARC manipulation library |
| owslib | Latest | CSW client library |

## 📁 Project Structure

```text
.agents/
└── skills/                # Agent Skills (agentskills.io standard)
    ├── arctrl/            # arctrl Python library reference
    └── config-wrapper/    # ConfigWrapper / ConfigBase pattern

openspec/                  # OpenSpec — spec-driven development
├── config.yaml            # Project context + artifact rules
├── specs/                 # Current behaviour (source of truth)
└── changes/               # In-flight change proposals

docs/
└── ai_workflow.md         # AI agent workflow documentation

middleware/
├── harvester/             # Central orchestrator and configuration
│   └── src/middleware/harvester/
│       ├── main.py            # CLI entrypoint
│       ├── orchestrator.py    # Multi-repository harvest loop
│       ├── upload.py          # Plugin stream → API upload
│       ├── reporting.py       # Shared HarvestReport wiring / emit
│       ├── plugin_base.py     # Plugin protocol + HarvestedArc
│       ├── config.py
│       ├── errors.py
│       ├── nice_http_client.py
│       └── healthcheck.py
├── inspire/               # INSPIRE to ARC harvester (Core logic)
│   ├── src/middleware/inspire/
│   │   ├── plugin.py      # Plugin generator (run_plugin AsyncGenerator)
│   │   ├── csw_client.py  # CSW client and ISO 19139 parser
│   │   ├── mapper.py      # INSPIRE to ARC mapping logic
│   │   ├── models.py      # Pydantic domain models (InspireRecord, Contact, etc.)
│   │   ├── config.py      # Configuration model
│   │   └── errors.py      # Custom exceptions
│   └── tests/
│       ├── unit/          # Unit tests for mapper and harvester
│       └── integration/   # Integration tests with real CSW endpoints
└── linked_data/           # Linked-data / sitemap / Regal harvester
```

## 🔧 Important Commands

### Always use `uv` for Python

```bash
# Run tests
uv run pytest middleware/ -v

# Quality checks (all read config from pyproject.toml — see openspec/specs/principles/)
uv run ruff format --check middleware/
uv run ruff check middleware/
uv run mypy --config-file pyproject.toml
uv run pylint middleware/inspire middleware/linked_data middleware/harvester
uv run bandit -r middleware/ -c .bandit -ll

# Or wrap commit-stage pre-commit hooks:
./scripts/quality-fix.sh
./scripts/quality-check.sh

# Install/Update all dependencies
uv sync --dev --all-packages
```

Note: Cursor Source Control may skip git hooks (≥3.15.6: forces `core.hooksPath=/dev/null`).
Dev Container `remoteEnv` prepends `scripts/bin` so SCM uses `scripts/cursor-git.sh`, which
strips that pin. Terminal `git` is unaffected. Remove once Cursor fixes
[forum #167719](https://forum.cursor.com/t/167719).

### Execution

```bash
uv run python -m middleware.harvester.main -c config.yaml
```

### OpenSpec

```bash
# List current specs / active changes
openspec list --specs
openspec list

# Validate
openspec validate --specs
```

In Cursor chat: `/opsx-propose`, `/opsx-apply`, `/opsx-archive`, `/opsx-explore`.
In GitHub Copilot: the same via `.github/prompts/opsx-*.prompt.md`.

## Architecture & Design

**Read [`openspec/specs/principles/`](openspec/specs/principles/) first.** It defines the plugin
contract, module dependency rules, values, constraints, and code quality requirements. Do not
restate what is there.

Before generating or modifying code, read the relevant OpenSpec domains under `openspec/specs/`.
For new work, prefer `/opsx-propose` so changes land as deltas in `openspec/changes/` and are
archived into main specs.

**Project-level** (cross-cutting):

- **[`openspec/specs/principles/`](openspec/specs/principles/)** — Authoritative project principles (start here).
- **[`openspec/specs/error-handling/`](openspec/specs/error-handling/)** — Centralized exception hierarchy and generator yielding patterns.
- **[`openspec/specs/demo-environment/`](openspec/specs/demo-environment/)** — One-command local demo environment (mock API + harvester).
- **[`openspec/specs/async-concurrency/`](openspec/specs/async-concurrency/)** —
  `asyncio.to_thread()` for OWSLib, concurrent dataset fetching via Semaphore+TaskGroup,
  `asyncio.gather()` for repositories, `harvest_arcs` for pipelined batch uploads.
- **[`openspec/specs/nice-http-client/`](openspec/specs/nice-http-client/)** —
  `NiceHttpClient` and `NiceHttpClientConfig`: shared polite-HTTP wrapper (timeout,
  retry/backoff, rate limiting, user-agent, optional robots.txt) used by all plugins that make
  direct HTTP requests.
- **[`openspec/specs/skipped-datasets/`](openspec/specs/skipped-datasets/)** —
  `SkippedRecord` signal type, `skipped_datasets` counter in `RepositoryReport`, and
  `fairagro:skippedDatasets` in the JSON-LD harvest report.

**Harvester** (orchestrator internals):

- **[`openspec/specs/harvester-orchestration/`](openspec/specs/harvester-orchestration/)** — Orchestration loop and plugin `AsyncGenerator` contract.
- **[`openspec/specs/harvester-configuration/`](openspec/specs/harvester-configuration/)** — Configuration file structure, plugin field typing, and mutual-exclusion validation.
- **[`openspec/specs/otlp-observability/`](openspec/specs/otlp-observability/)** — OTLP tracing via `middleware.shared.tracing`; span structure, attribute names, and shutdown contract.
- **[`openspec/specs/harvest-report/`](openspec/specs/harvest-report/)** — How the
  orchestrator drives `HarvestReport` / `RepositoryScope` counting methods
  (`record_failed` vs `record_repository_issue`) and emits via
  `JsonLdReportSerializer` (vocab `ns/harvest-report/v2/`); contract owned by
  [`m4.2_advanced_middleware_api`](https://github.com/fairagro/m4.2_advanced_middleware_api).
- **[`openspec/specs/liveness-probe/`](openspec/specs/liveness-probe/)** — Kubernetes
  liveness probe: asyncio heartbeat loop (file mtime) + PyInstaller `healthcheck` binary;
  `heartbeat_path` and `heartbeat_interval` config fields.

**INSPIRE plugin**:

- **[`openspec/specs/csw-harvesting/`](openspec/specs/csw-harvesting/)** — Polling
  standard CSW endpoints and ISO 19139 batch fetching logic; lazy Dublin Core fallback for
  identifier recovery on broken records.
- **[`openspec/specs/csw-retry/`](openspec/specs/csw-retry/)** — Retry with exponential backoff for transient CSW failures; `user_agent` forwarding via OWSLib headers.
- **[`openspec/specs/csw-threadpool/`](openspec/specs/csw-threadpool/)** — Per-client bounded `ThreadPoolExecutor` for OWSLib calls; `csw_thread_pool_size` config field.
- **[`openspec/specs/inspire-to-arc-mapping/`](openspec/specs/inspire-to-arc-mapping/)** — Rules transforming InspireRecord to ArcInvestigation/Study/Assay/Protocols.
- **[`openspec/specs/inspire-workflow-execution/`](openspec/specs/inspire-workflow-execution/)** — The INSPIRE plugin processing loop.

**Linked-data plugin**:

- **[`openspec/specs/linked-data-harvesting/`](openspec/specs/linked-data-harvesting/)** — Top-level harvesting loop: sitemap discovery → dataset fetch → mapper → upload.
- **[`openspec/specs/xml-sitemap-parser/`](openspec/specs/xml-sitemap-parser/)** — XML sitemap protocol; `urlset` / `sitemapindex` traversal and deduplication.
- **[`openspec/specs/sitemap-mycore-solr/`](openspec/specs/sitemap-mycore-solr/)** — MyCoRe Solr JSON discovery source; Solr pagination, `id`→`/receive/{id}` URL construction.
- **[`openspec/specs/html-jsonld-dataset/`](openspec/specs/html-jsonld-dataset/)** — HTML page scraping and embedded JSON-LD extraction.
- **[`openspec/specs/linked-data-dataset-abstraction/`](openspec/specs/linked-data-dataset-abstraction/)** — `Dataset` base class and `DiscoveryResult` abstraction.
- **[`openspec/specs/linked-data-mapper/`](openspec/specs/linked-data-mapper/)** — Mapping rdflib `Graph` to ARC RO-Crate JSON-LD.
- **[`openspec/specs/regal-jsonld/`](openspec/specs/regal-jsonld/)** — Regal `/find` discovery, inline Regal JSON-LD datasets, and Regal→ARC mapping (e.g. PUBLISSO FRL).
- **[`openspec/specs/regal-to-arc-mapping/`](openspec/specs/regal-to-arc-mapping/)** — Regal ResearchData → ARC implementation contract; authoritative field rules in [`docs/regal_mapping.md`](docs/regal_mapping.md).

---

## 📝 Key Implementation Details

### External Dependencies

This project depends on `shared` and `api_client` libraries, which are hosted in a separate repository (`m4.2_advanced_middleware_api`). They are included via `uv` workspace sources pointing to Git.

## 📚 File Modifications Pattern

When editing files:

1. **Always check current state** - Use file viewing tools to see current content.
2. **Review for quality** - Check the VS Code **Problems** tab.
3. **Format and test after changes** - Run `uv run ruff format middleware/` to auto-format, then `uv run pytest` to verify.

---

**Last Updated**: 2026-07-29
**Maintainer Notes**: This repository is the standalone Middleware Harvester. It is decoupled from the main Middleware API. Spec-driven development uses [OpenSpec](https://github.com/Fission-AI/OpenSpec).
