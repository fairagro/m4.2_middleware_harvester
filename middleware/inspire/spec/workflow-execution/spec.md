# Plugin Execution

Exposes an asynchronous generator that iterates over CSW records and yields serialized ARCs. As a plugin, it must not execute standalone (no `main()` function) and relies on the global Harvester for API interactions.

## Requirements

- [ ] Implement `InspirePlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.
- [ ] Use the `CSWClient` class to communicate with the CSW endpoint and fetch all available metadata records iteratively.
- [ ] Skip any record whose `hierarchy` is not a valid data type (i.e., not within `["dataset", "series", "nongeographicdataset"]`).
- [ ] Use the `InspireMapper` class to transform each valid parsed record into an ARC object.
- [ ] Serialize each ARC via `arc.ToROCrateJsonString()` and `yield` the resulting JSON string to the calling Harvester.
- [ ] Do not include a `main()` function, argument parsing, or `ApiClient` upload logic.
