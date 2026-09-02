## 1. Plugin pipeline — bounded queue

- [ ] 1.1 In `_run_with_task_group`, create `results` with `maxsize=worker_tasks` instead of unbounded queue
- [ ] 1.2 Verify worker `put` → `finally` release ordering still provides backpressure when queue is full (no early semaphore release)

## 2. Plugin pipeline — abort cancellation

- [ ] 2.1 On `GeneratorExit` during consumer `yield`, cancel TaskGroup producer and worker tasks instead of bare `return`
- [ ] 2.2 Ensure `active_workers` / semaphore invariants hold on `CancelledError` (no deadlock on shutdown)
- [ ] 2.3 Confirm normal full-drain completion path is unchanged

## 3. Unit tests

- [ ] 3.1 Add test: slow consumer — assert max concurrent `_process_result` / mapped outcomes ≤ 2 × `effective_worker_tasks`
- [ ] 3.2 Add test: early `aclose()` on large catalog — assert map count ≪ catalog size and no asyncio loop exceptions
- [ ] 3.3 Add test: arrival order preserved under backpressure (optional if covered by 3.1 setup)
- [ ] 3.4 Keep existing `test_linked_data_plugin_aclose_after_first_result` passing

## 4. Spec design notes

- [ ] 4.1 Add Key Decision to `openspec/specs/linked-data-harvesting/design.md` documenting bounded queue + 2× bound (during archive sync)

## 5. Validation

- [ ] 5.1 `uv run ruff format middleware/linked_data/`
- [ ] 5.2 `uv run pytest middleware/linked_data/tests/unit/test_linked_data_plugin.py -v`
- [ ] 5.3 `openspec validate linked-data-pipeline-backpressure --strict`
