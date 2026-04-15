# API Upload

Handles submitting correctly parsed ARCs to the central system via `api_client`.

## Requirements

- [ ] Upon generating an ARC, invoke `client.create_or_update_arc` against the target Endpoint.
- [ ] Attach the target `RDI` via the configurator parameter.
- [ ] Handle potential runtime errors, failing locally but continuing sequentially.
