# Tech Stack

## Core Language

- **Python 3.12+** — async/await, type safety, Pydantic validation

## HTTP & Parsing

- **httpx** — async HTTP client for sitemap/dataset fetching
- **rdflib** — parse JSON-LD into RDF Graph for mapping

## ARC Construction

- **arctrl** — build ArcInvestigation, ArcStudy, ArcAssay objects

## Deployment

- **cron** — scheduled harvest execution
- **Docker** — containerization for reproducibility

## Quality

- **uv** — dependency management
- **ruff/mypy/pylint/bandit** — code quality (inherited from project standards)