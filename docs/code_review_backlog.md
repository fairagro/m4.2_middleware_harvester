# Code Review Backlog

Items identified during the 2025 code review that were deferred for later action.
Implemented items are tracked in git history (`feature/improvements` branch).

---

## Item 2 — Thread-pool saturation under concurrent load

**Category:** Performance / Medium  
**Location:** `middleware/inspire/src/middleware/inspire/csw_client.py`  
**Function:** `get_records_async`, `get_record_count_async`

**Problem:**  
All blocking OWSLib calls use `asyncio.to_thread()`, which submits work to the
default thread pool (`concurrent.futures.ThreadPoolExecutor`). The pool size
defaults to `min(32, os.cpu_count() + 4)`. Under high concurrency (many
repositories harvested in parallel), threads may be exhausted, causing
`asyncio.to_thread` calls to queue silently and reducing throughput.

**Recommendation:**  
Consider passing a dedicated, bounded `ThreadPoolExecutor` (e.g. via
`loop.run_in_executor(pool, ...)`) whose size is controlled by configuration.
This prevents pool exhaustion and makes thread use observable via metrics.

---

## Item 5 — Fragile CSW record-order assumption in `_yield_records_with_stable_ids`

**Category:** Correctness / Medium  
**Location:** `middleware/inspire/src/middleware/inspire/csw_client.py`  
**Function:** `_yield_records_with_stable_ids`

**Problem:**  
The method pairs DC IDs (from one request) with ISO records (from a second
request) by positional index. This relies on the CSW server returning records in
the same order for both requests. The CSW 2.0.2 spec does not guarantee this.
An alignment mismatch warning is already emitted, but the harvest continues with
a potentially wrong ID.

**Recommendation:**  
Add an explicit `SortBy` clause (e.g. `dc:identifier ASC`) to both
`_fetch_dc_ids` and `_fetch_iso_batch` requests to enforce a deterministic,
server-side order. Alternatively, skip the DC pre-fetch entirely and rely on the
`identifier` field parsed from the ISO record directly (where available).

---

## Item 6 — Name parsing bug for compound surnames in `mapper.py`

**Category:** Correctness / Medium  
**Location:** `middleware/inspire/src/middleware/inspire/mapper.py`  
**Function:** `_split_name` (or equivalent contact-name parsing logic)

**Problem:**  
The current name-splitting logic splits on whitespace and assumes
`first_name = parts[0]`, `last_name = parts[-1]`. For compound surnames such as
`"Maria Garcia Brizuela"` or `"Hans-Joachim von Müller"`, the middle tokens are
lost or assigned to the wrong field.

**Recommendation:**  
Use a dedicated name-parsing library (e.g. `nameparser`) or at minimum reverse
the heuristic: assume everything except the first token is the last name
(`last_name = " ".join(parts[1:])`). Add unit tests covering double-barrelled
names, particles (`von`, `de`, `van`), and single-token names.

---

## Item 9 — `plugin_config.py` provides minimal value as a standalone file

**Category:** Refactoring / Low  
**Location:** `middleware/harvester/src/middleware/harvester/plugin_config.py`

**Problem:**  
`plugin_config.py` defines a single `PluginConfig` Protocol (or base class) used
only as a type annotation in `config.py`. The indirection adds a file and import
without meaningful abstraction benefit given the current two-plugin setup.

**Recommendation:**  
Inline the `PluginConfig` definition directly into `config.py`, or promote it to
the `middleware.shared` package if it is intended to be part of a formal plugin
contract. Remove the standalone file to reduce cognitive overhead.
