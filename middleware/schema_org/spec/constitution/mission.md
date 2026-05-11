# Schema.org Harvester — Mission

Harvest schema.org-formatted metadata from Research Data Infrastructure (RDI)
providers, transform each record into an Annotated Research Context (ARC)
object, and publish the results to the FAIRagro Middleware API.

## Goals

- **Interoperability**: Convert heterogeneous schema.org metadata into
  standardized ARC format understood by FAIRagro.
- **Extensibility**: Support new RDIs by adding per-RDI mapper implementations.
- **Reliability**: Yield errors at record level; never abort an entire harvest run.

## Scope

- Input: schema.org JSON-LD from RDI landing pages
- Output: ARC (RO-Crate JSON-LD) published to Middleware API
- Consumers: FAIRagro Middleware API only (for now)

## Out of Scope

- Multi-protocol support (CSW, OAI-PMH) — handled by other harvester plugins
- Direct human consumers — metadata flows machine-to-machine