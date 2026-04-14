# FAIRagro INSPIRE-to-ARC — Principles

## Purpose

Harvest metadata from INSPIRE-compliant Catalogue Service for Web (CSW) endpoints, translate the ISO 19139 XML into the Annotated Research Context (ARC) format, and publish the results to the FAIRagro Middleware API.

## Values

**Correctness over speed** — Valid ARC output matters more than throughput. We properly model the metadata via Pydantic (`InspireRecord`) to ensure semantic validity before parsing.

**Failure isolation** — One bad record in a harvest batch must not abort the entire run. Errors are caught via `RecordProcessingError`, logged along with the specific record URL, and skipped securely. The process then continues.

**Stateless batch process** — The harvester stores no state between runs. No lock files, no local sqlite. The only persistent output is what the Middleware API receives.

**Memory safety and API Respect** - CSW endpoints can contain millions of records. Parsing is handled efficiently and uses pagination mechanisms under the hood so as not to overwhelm memory.

## Module Dependency Graph

```text
main -> config
main -> harvester
main -> mapper
main -> api_client
harvester -> errors
mapper -> harvester (for InspireRecord definition)
```

Circular imports are forbidden. The mapper does not initiate harvesting loops, and the harvester knows nothing about ARCs.
