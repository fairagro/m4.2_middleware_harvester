"""Demo API Mock for the FAIRagro harvester.

This module provides a lightweight FastAPI server that simulates the Middleware
API. It receives ARC RO-Crate payloads, deserialises them using the arctrl
library, and writes the resulting ARC directory structure to the local file
system.

It implements the ``v3/harvests`` lifecycle that ``ApiClient.harvest_arcs()``
actually drives -- ``POST /v3/harvests``, ``POST /v3/harvests/{id}/arcs``,
``POST /v3/harvests/{id}/complete``, ``GET /v3/harvests/{id}`` and
``PATCH /v3/harvests/{id}`` -- alongside the older single-shot
``POST /v3/arcs``. Response bodies mirror the ``HarvestResult`` / ``ArcResult``
pydantic models in ``middleware.api_client.models``; the client validates them,
so field names and enum spellings matter.

Two deliberate deviations from the real API, both so local runs stay usable:

* An unknown harvest id is never answered with 404. ``ApiClient`` classifies 404
  as a catastrophic harvest error and aborts the whole run, which makes a
  restarted mock impossible to work with. Unknown ids are adopted instead.
* Output is grouped per run under ``<rdi>/<harvest_id>/`` and each run gets a
  ``harvest.json`` summary, so two harvests of the same RDI (for example the
  same config run against two git branches) stay comparable.
"""

# This file is a standalone demo artefact, not part of the main package.
# Its dependencies (fastapi, uvicorn) are only available inside the demo
# container or via `uv run --with`, not in the project virtualenv.  Suppressing
# all import/type errors at the file level is intentional.
# pylint: disable=import-error
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import json
import os
import re
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arctrl import ARC
from fable_library.async_ import start_as_task
from fastapi import FastAPI, Request

app = FastAPI()

# Root directory under which all ARC data and error logs are stored.
# Overridable so the mock can run outside the demo container.
OUTPUT_ROOT = Path(os.environ.get("DEMO_OUTPUT_DIR", "/data/arcs"))

# In-memory harvest registry: harvest_id -> harvest state.
_HARVESTS: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _get_target_owner() -> tuple[int, int] | None:
    uid_value = os.environ.get("LOCAL_UID")
    gid_value = os.environ.get("LOCAL_GID")
    if uid_value is None or gid_value is None:
        return None
    try:
        return int(uid_value), int(gid_value)
    except ValueError:
        print(f"Invalid LOCAL_UID/LOCAL_GID: {uid_value}/{gid_value}")
        return None


def _chown_tree(path: Path) -> None:
    owner = _get_target_owner()
    if owner is None or not path.exists():
        return
    uid, gid = owner

    os.chown(path, uid, gid)
    if path.is_dir():
        for root, dirs, files in os.walk(path):
            root_path = Path(root)
            os.chown(root_path, uid, gid)
            for name in dirs:
                os.chown(root_path / name, uid, gid)
            for name in files:
                os.chown(root_path / name, uid, gid)


def _handle_error(arc_dir: Path, rdi: str, arc_id: str, exc: Exception) -> None:
    tb = traceback.format_exc()
    print(f"Error writing ARC for {rdi}/{arc_id} (dir={arc_dir}): {exc}\n{tb}")


# Pre-compiled pattern for safe ARC directory names (no path traversal, predictable charset).
_SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def _generate_random_arc_id() -> str:
    return f"arc_{os.urandom(4).hex()}"


def _derive_safe_arc_id(base_dir: Path, raw_id: object) -> tuple[str, Path]:
    """Derive a safe ARC identifier and corresponding directory path.

    Always returns a valid (arc_id, path) pair contained within base_dir.
    Falls back to a random ID when the provided raw_id cannot be used safely.
    """

    def _fallback() -> tuple[str, Path]:
        rid = _generate_random_arc_id()
        return rid, base_dir / rid

    if not (isinstance(raw_id, str) and raw_id.strip()):
        return _fallback()

    # os.path.basename strips all directory components, preventing path traversal.
    safe_name = os.path.basename(raw_id.strip())
    if not safe_name or safe_name in {".", ".."} or not _SAFE_NAME_PATTERN.match(safe_name):
        return _fallback()

    return safe_name, base_dir / safe_name


def _safe_path_segment(raw: object, fallback: str) -> str:
    """Return a filesystem-safe single path segment, or ``fallback``."""
    if not (isinstance(raw, str) and raw.strip()):
        return fallback
    segment = os.path.basename(raw.strip())
    if not segment or segment in {".", ".."} or not _SAFE_NAME_PATTERN.match(segment):
        return fallback
    return segment


async def _write_arc(output_path: Path, rdi: str, arc_payload: dict) -> tuple[str, str]:
    """Persist one ARC payload and its reconstructed directory.

    Returns ``(arc_id, timestamp)``. Write failures are logged, not raised: a
    malformed ARC should show up in the harvester's own report rather than as a
    mock-side 500 that the client would classify as a submission failure.
    """
    output_path.mkdir(parents=True, exist_ok=True)
    _chown_tree(output_path)

    now = _now()
    arc_id, arc_dir = _derive_safe_arc_id(output_path, arc_payload.get("identifier"))

    payload_path = arc_dir.with_suffix(".payload.json")
    with open(payload_path, "w", encoding="utf-8") as handle:
        json.dump(arc_payload, handle, indent=2)
    _chown_tree(payload_path)

    try:
        arc_json = json.dumps(arc_payload)
        arc = ARC.from_rocrate_json_string(arc_json)
        await start_as_task(arc.WriteAsync(str(arc_dir)))
        _chown_tree(arc_dir)
        print(f"Saved ARC structure for {rdi} as {arc_id} using arctrl")
    except (json.JSONDecodeError, OSError, RuntimeError) as exc:
        _handle_error(arc_dir, rdi, arc_id, exc)
    except Exception as exc:  # noqa: BLE001
        _handle_error(arc_dir, rdi, arc_id, exc)

    return arc_id, now


def _arc_result(arc_id: str, now: str, status: str = "created") -> dict[str, object]:
    """Build an ``ArcResult``-shaped response body."""
    return {
        "arc_id": arc_id,
        "status": status,
        "metadata": {
            "arc_hash": "demo_hash",
            "status": "ACTIVE",
            "first_seen": now,
            "last_seen": now,
        },
        "events": [],
        "message": "",
        "client_id": None,
    }


def _harvest_result(harvest: dict[str, Any]) -> dict[str, object]:
    """Build a ``HarvestResult``-shaped response body from stored state."""
    return {
        "harvest_id": harvest["harvest_id"],
        "rdi": harvest["rdi"],
        "status": harvest["status"],
        "started_at": harvest["started_at"],
        "completed_at": harvest["completed_at"],
        "statistics": {
            "expected_datasets": harvest["expected_datasets"],
            "arcs_submitted": harvest["arcs_submitted"],
            "arcs_new": harvest["arcs_submitted"],
            "arcs_updated": 0,
            "arcs_unchanged": 0,
            "arcs_missing": 0,
            "errors": 0,
        },
        "errors": [],
        "message": "",
        "client_id": None,
    }


def _harvest_dir(harvest: dict[str, Any]) -> Path:
    rdi_segment = _safe_path_segment(harvest["rdi"], "unknown-rdi")
    id_segment = _safe_path_segment(harvest["harvest_id"], "unknown-harvest")
    return OUTPUT_ROOT / rdi_segment / id_segment


def _adopt_harvest(harvest_id: str) -> dict[str, Any]:
    """Return the stored harvest, inventing one for an unknown id.

    ``ApiClient`` treats 404 as a catastrophic harvest error and aborts the run,
    so a mock restarted mid-harvest would kill the harvester. Adopting the id
    keeps local runs going.
    """
    harvest = _HARVESTS.get(harvest_id)
    if harvest is not None:
        return harvest

    print(f"Adopting unknown harvest id {harvest_id} (mock restarted?)")
    harvest = {
        "harvest_id": harvest_id,
        "rdi": "unknown-rdi",
        "status": "RUNNING",
        "started_at": _now(),
        "completed_at": None,
        "expected_datasets": None,
        "arcs_submitted": 0,
    }
    _HARVESTS[harvest_id] = harvest
    return harvest


def _write_harvest_summary(harvest: dict[str, Any]) -> None:
    """Write a per-run summary next to the run's ARCs."""
    harvest_dir = _harvest_dir(harvest)
    harvest_dir.mkdir(parents=True, exist_ok=True)
    summary_path = harvest_dir / "harvest.json"
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(_harvest_result(harvest), handle, indent=2)
    _chown_tree(summary_path)


@app.post("/v3/harvests")
async def create_harvest(request: Request) -> dict[str, object]:
    """Start a harvest run.

    Body is ``{"rdi": "...", "expected_datasets": int | null}``. An optional
    ``Idempotency-Key`` header is accepted and ignored -- the client only sends
    one when it loaded a client certificate chain, which local runs do not.
    """
    data = await request.json()
    harvest_id = f"demo-harvest-{uuid.uuid4().hex[:12]}"
    harvest = {
        "harvest_id": harvest_id,
        "rdi": data.get("rdi", "unknown-rdi"),
        "status": "RUNNING",
        "started_at": _now(),
        "completed_at": None,
        "expected_datasets": data.get("expected_datasets"),
        "arcs_submitted": 0,
    }
    _HARVESTS[harvest_id] = harvest
    _harvest_dir(harvest).mkdir(parents=True, exist_ok=True)
    print(f"Created harvest {harvest_id} for rdi={harvest['rdi']} expected={harvest['expected_datasets']}")
    return _harvest_result(harvest)


@app.post("/v3/harvests/{harvest_id}/arcs")
async def submit_harvest_arc(harvest_id: str, request: Request) -> dict[str, object]:
    """Submit one ARC into a harvest run.

    Body is ``{"arc": {...}}`` -- unlike ``POST /v3/arcs`` it carries no ``rdi``,
    which is resolved from the stored harvest instead.
    """
    data = await request.json()
    harvest = _adopt_harvest(harvest_id)
    arc_payload: dict = data.get("arc", data)

    arc_id, now = await _write_arc(_harvest_dir(harvest), harvest["rdi"], arc_payload)
    harvest["arcs_submitted"] += 1
    return _arc_result(arc_id, now)


@app.post("/v3/harvests/{harvest_id}/complete")
async def complete_harvest(harvest_id: str) -> dict[str, object]:
    """Mark a harvest run completed and write its summary."""
    harvest = _adopt_harvest(harvest_id)
    harvest["status"] = "COMPLETED"
    harvest["completed_at"] = _now()
    _write_harvest_summary(harvest)
    print(f"Completed harvest {harvest_id}: {harvest['arcs_submitted']} ARC(s)")
    return _harvest_result(harvest)


@app.patch("/v3/harvests/{harvest_id}")
async def update_harvest(harvest_id: str, request: Request) -> dict[str, object]:
    """Apply a status change (``FAILED`` / ``CANCELLED``) to a harvest run."""
    data = await request.json()
    harvest = _adopt_harvest(harvest_id)
    status = data.get("status")
    if status in {"FAILED", "CANCELLED", "COMPLETED", "RUNNING"}:
        harvest["status"] = status
    if harvest["status"] in {"FAILED", "CANCELLED", "COMPLETED"}:
        harvest["completed_at"] = _now()
    _write_harvest_summary(harvest)
    print(f"Harvest {harvest_id} -> {harvest['status']}")
    return _harvest_result(harvest)


@app.get("/v3/harvests/{harvest_id}")
async def get_harvest(harvest_id: str) -> dict[str, object]:
    """Return a harvest run by id."""
    return _harvest_result(_adopt_harvest(harvest_id))


@app.post("/v3/arcs")
async def upload_arc(request: Request) -> dict[str, object]:
    """Handle a single-shot ARC submission outside any harvest run.

    Receives the RO-Crate JSON-LD payload as ``{"rdi": "...", "arc": {...}}``,
    validates it, and uses the arctrl library to reconstruct the ARC directory
    structure. Results are saved to the local ``demo_output`` volume.
    """
    data = await request.json()
    rdi: str = data.get("rdi", "unknown")
    arc_payload: dict = data.get("arc", data)

    output_path = OUTPUT_ROOT / _safe_path_segment(rdi, "unknown-rdi") / "_direct"
    arc_id, now = await _write_arc(output_path, rdi, arc_payload)
    return _arc_result(arc_id, now)


@app.get("/live")
def live() -> dict[str, str]:
    """Liveness probe for the demo API."""
    return {"status": "ok"}
