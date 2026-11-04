# Design

## Context

`ApiClient.harvest_arcs` (api_client, m4.2_advanced_middleware_api) creates the harvest, submits the ARC stream and then
always calls `complete`. It calls `fail` only when the ARC stream (or a submission) raises. A plugin's yielded
`HarvesterError` is consumed by the harvester's stream filter, so today the client never sees it.

## Goals / Non-Goals

**Goals:** fail the API harvest after a recorded repository-level issue without changing the plugin contract.

**Non-Goals:** changing api_client in this change; changing how the plugin stream is consumed.

## Decisions

- **Raise at the end of the filtered stream.** When the plugin stream is exhausted and at least one repository-level
  issue was recorded for it, the stream filter raises a dedicated harvester exception, so `harvest_arcs` fails the
  harvest. Raising at the end, not at the error, lets the plugin hand over every ARC it still produces, so the stored
  ARCs are as fresh as possible for the next finalize. Alternatives: driving `create`/`submit`/`fail` by hand duplicates
  the client's concurrency and duplicate-detection shim (#240); adding a fail flag to api_client first blocks this fix
  on an API release.
- **That exception is not an upload abort.** The upload error path recognises it: it does not call
  `record_upload_aborted` (the plugin's issue is already recorded once), and ARCs handed to the client count as
  harvested. The client returns no per-item errors when it raises, so this count is "submitted", not "API-accepted".

## Risks / Trade-offs

- [In-flight submissions race the fail: `_submit_arcs_parallel` neither awaits nor cancels pending submit tasks when the
  stream raises, so up to `max_concurrency` trailing ARCs may be rejected by a FAILED harvest and per-item errors are
  lost] → upstream api_client issue to drain pending submissions before failing; the dev-stack check (task 2.1) shows
  the effect on a real run.
- [A failed harvest leaves the dump unrefreshed until the RDI's next COMPLETED run] → accepted: stored ARCs are kept and
  appear then (#546 spike).
