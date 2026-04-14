# Workflow Execution

Orchestrates the entire harvesting logic.

## Requirements

- [ ] Use the `CSWClient` class to communicate with the CSW endpoint and fetch all available metadata records iteratively.
- [ ] Skip any record whose `hierarchy` is not a valid data type (i.e., not within `["dataset", "series", "nongeographicdataset"]`).
- [ ] Use the `InspireMapper` class to transform each valid parsed record into an ARC object.
- [ ] Upload the generated ARCs to the FAIRagro Middleware API using the configured API client.
- [ ] Error isolation: If the mapping or uploading of a single record fails, the orchestrator must log the error (including the record identifier to ease debugging) and continue processing the rest of the records without aborting the entire run.
