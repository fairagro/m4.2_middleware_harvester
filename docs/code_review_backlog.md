# Code Review Backlog

Items identified during code reviews that were deferred for later action.
Implemented items are tracked in git history (`feature/improvements` branch).

---

## ~~Item 1~~ ✅ — Plugin registration is spread across 6 locations

**Fixed in commit `76f7c10`**

`plugin_type` and `plugin_config` now derived dynamically from `model_fields`.
`source_url` property added to `RepositoryConfig`. `_get_repo_source_url()` deleted from `main.py`.
Adding a new plugin now only requires: (1) a new `Optional` field in `RepositoryConfig`, (2) an entry in `_PLUGIN_CLASSES`.

---

## ~~Item 3~~ ✅ — `Plugin` ABC uses `if False: yield` workaround

**Fixed in commit `95784c7`**

`Plugin` converted from `abc.ABC` to `typing.Protocol`. The `if False: yield` dead-code hack is gone.
`run` declared as a regular (non-`async`) method returning `AsyncGenerator` — this matches the call sites (`plugin.run()` without `await`) and is structurally compatible with async generator function implementations.
Concrete plugins and test doubles retain their explicit `(Plugin)` inheritance, which is valid for Protocol subclasses.

---

## ~~Item 4~~ ✅ — `cast()` in `_run_repository` works around a missing constructor contract

**Fixed in commit `55fa183`**

`_PLUGIN_CLASSES: dict[str, type[Plugin]]` renamed to `_PLUGIN_FACTORIES: dict[str, Callable[..., Plugin]]`.
`cast()` removed from the instantiation site. Unused `PluginConfig` import dropped from `main.py`.
Also corrected `isinstance(result, Exception)` → `isinstance(result, BaseException)` in the gather loop.

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

## ~~Item 9 — `plugin_config.py` as a standalone file~~ ✅ Fixed

**Resolved in:** commit `3ef406a`  
`PluginConfig` inlined into `config.py`; `plugin_config.py` deleted.

---

## ~~Item 7 — Duplicated dispatch logic in `get_records` / `get_records_async`~~ ✅ Fixed

**Resolved in:** commit `35b6f0d`  
`_pick_strategy()` helper extracted; shared by both methods.

