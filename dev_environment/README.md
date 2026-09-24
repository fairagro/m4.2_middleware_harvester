# Development Environment

Local ways to run the harvester: against static fixtures, against the real RDIs, or as a credential-free demo.

There are three stacks. Pick by what you need:

| Stack                           | Network            | Credentials              | Writes ARCs to                 | Use it for                                                |
| ------------------------------- | ------------------ | ------------------------ | ------------------------------ | --------------------------------------------------------- |
| `compose.fixtures.yaml`         | none               | none                     | `demo_output/`                 | Exercising mapper behaviour end to end, deterministically |
| `compose.demo.yaml`             | public GeoNode CSW | none                     | `demo_output/`                 | A quick smoke test of the whole pipeline                  |
| `compose.yaml` (via `start.sh`) | real RDIs          | **sops key + mTLS cert** | `middleware-test.fairagro.net` | Running against the real middleware                       |

## Building the image

`docker compose --build` **cannot build the harvester.** `docker/Dockerfile.harvester` consumes the named build contexts
`export_bins` and `healthcheck_bins`, and those are wired only in `docker-bake.hcl`. Build with Bake first, then bring
the stack up without `--build`:

```bash
cd "$(git rev-parse --show-toplevel)"
set -a && source versions.env && set +a
docker buildx bake harvester --load --set harvester.tags=harvester:fixtures
```

Swap the tag to match the stack you are starting (`harvester:fixtures`, `harvester:demo`, or `harvester:latest`).

## Fixture stack — no network, no credentials

Harvests a static stand-in for OpenAgrar: a `mycore_solr` discovery endpoint plus record pages with embedded JSON-LD.
See [`fixtures/openagrar/README.md`](fixtures/openagrar/README.md) for what each record covers and which parts are real.

```bash
docker buildx bake harvester --load --set harvester.tags=harvester:fixtures
docker compose -f dev_environment/compose.fixtures.yaml up --abort-on-container-exit
```

Or without Docker, which is the faster loop when iterating on mapper code:

```bash
uv sync --dev --all-packages

# terminal 1 — fixture origin
uv run python -m http.server 8080 --directory dev_environment/fixtures/openagrar

# terminal 2 — mock Middleware API
DEMO_OUTPUT_DIR=$PWD/dev_environment/demo_output \
  uv run --with fastapi --with uvicorn \
  uvicorn demo_api_main:app --app-dir dev_environment --host 127.0.0.1 --port 8000

# terminal 3 — the harvester
uv run python -m middleware.harvester.main -c dev_environment/config.fixtures.yaml \
  > report.json 2> run.log
```

`config.fixtures.yaml` targets `localhost`; `config.fixtures.container.yaml` is the same config with compose service
names. Keep the two in sync.

## Demo stack — public CSW, no credentials

```bash
docker buildx bake harvester --load --set harvester.tags=harvester:demo
docker compose -f dev_environment/compose.demo.yaml up --abort-on-container-exit
```

Harvests five records from the public GeoNode demo catalogue (`config.demo.yaml`) into the mock API.

## Real RDIs — needs credentials

```bash
cd dev_environment
./start.sh          # or ./start.sh --build
./stop.sh           # ./stop.sh --clean also drops volumes
```

`start.sh` wraps `docker compose -f compose.yaml up` in `sops exec-env` to decrypt `client.key`. **This posts to
`https://middleware-test.fairagro.net` over mTLS — it is not a local demo.** It needs `sops` installed and a PGP secret
key for one of the recipients in [`.sops.yaml`](../.sops.yaml). Without those, use the fixture or demo stack.

`config.all-rdis.yaml` lists every RDI that can currently be harvested — bonares (INSPIRE/CSW), e!DAL and publisso
(linked data) — plus the OpenAgrar fixture. It points at the mock API, so it can be run from source against all of them
without credentials. Note it uses `repository-e.dataservice.zalf.de` for bonares: the `repository-staging...` host in
`config.yaml` no longer resolves.

Real OpenAgrar is commented out there. Every path the harvester uses — record pages, `servlets/solr/select`, and the
`sitemap_google.xml` in `robots.txt` — redirects to a proof-of-work challenge, so it cannot be harvested. Tracked in
[#271](https://github.com/fairagro/m4.2_middleware_harvester/issues/271).

## The mock Middleware API

`demo_api_main.py` is a FastAPI stand-in. It implements the `v3/harvests` lifecycle the client actually drives — create,
per-harvest ARC submit, complete, patch, get — plus the single-shot `POST /v3/arcs` and a `/live` probe, and
reconstructs each RO-Crate into an ARC directory with `arctrl`.

Output layout, under `DEMO_OUTPUT_DIR` (`/data/arcs` in the containers, bind-mounted to `demo_output/`):

```text
demo_output/<rdi>/<harvest_id>/
  harvest.json              run summary: status, counts, timestamps
  <arc_id>/                 the reconstructed ARC directory
  <arc_id>.payload.json     the RO-Crate exactly as submitted
```

Grouping per run keeps two harvests of the same RDI comparable — for example the same config run against two git
branches.

Two deliberate differences from the real API: an unknown harvest id is adopted rather than answered with 404 (the client
treats 404 as catastrophic and aborts the whole run, which makes a restarted mock unusable), and no authentication is
performed.

## Configuration

| File                             | Purpose                                                        |
| -------------------------------- | -------------------------------------------------------------- |
| `config.fixtures.yaml`           | Fixture RDI only, addressed via `localhost`                    |
| `config.fixtures.container.yaml` | Same, addressed via compose service names                      |
| `config.all-rdis.yaml`           | Every harvestable RDI plus the fixture, against the mock API   |
| `config.demo.yaml`               | Public GeoNode CSW, five records                               |
| `config.yaml`                    | Real RDIs against `middleware-test`, used by `compose.yaml`    |
| `config.local.yaml`              | Older local variant; not referenced by any compose file        |
| `config_example.yaml`            | Reference config with commented examples for every source type |

Any YAML leaf can be overridden by an environment variable, joining nested keys with `_` — for example
`API_CLIENT_API_URL=http://localhost:8000`. Values can also be supplied as files under `/run/secrets/<lowercase_key>`.

## Secrets

`client.key` is encrypted with sops (PGP recipients in [`.sops.yaml`](../.sops.yaml)):

```bash
sops client.key      # edit in place
sops -d client.key   # decrypt to stdout
```

`client.crt` is stored in plain text.

## Troubleshooting

**`docker compose --build` fails on the harvester** — expected; build with `docker buildx bake` first, as above.

**Harvester exits 1 immediately with 404s from the API** — the mock is out of date relative to `middleware.api_client`.
Check that it serves `POST /v3/harvests`; the client classifies 404 as catastrophic and aborts.

**`start.sh` fails to decrypt** — verify `sops -d client.key` works and that your PGP key is one of the `.sops.yaml`
recipients.

**Nothing appears in `demo_output/`** — confirm the harvester actually reached the API
(`docker compose logs harvester`), and that `DEMO_OUTPUT_DIR` points where you expect.

## Files

| File                        | Purpose                                                     |
| --------------------------- | ----------------------------------------------------------- |
| `compose.fixtures.yaml`     | Fixture origin + mock API + harvester                       |
| `compose.demo.yaml`         | Mock API + harvester against the public demo CSW            |
| `compose.yaml`              | Harvester against real RDIs and `middleware-test`           |
| `demo_api_main.py`          | Mock Middleware API                                         |
| `fixtures/openagrar/`       | Static OpenAgrar stand-in                                   |
| `start.sh` / `stop.sh`      | sops wrapper around `compose.yaml`                          |
| `client.crt` / `client.key` | mTLS client certificate; the key is sops-encrypted          |
| `FAIRagro.sql`              | Unused 252 MB LFS pointer from the retired Edaphobase stack |
