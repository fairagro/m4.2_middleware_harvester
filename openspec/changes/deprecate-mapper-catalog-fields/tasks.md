# Tasks

## 1. Deprecation warning

- [x] 1.1 Add a `MapperConfig` validator that emits `logger.warning` when `catalog_name` or `catalog_url` is set,
      pointing at the API's `known_rdis`; verify with a `caplog` unit test that validation still succeeds
- [x] 1.2 Confirm configs without the fields (or with blank values) do not warn; verify via unit test
- [x] 1.3 Confirm `CkanextDcatMapper` still writes `Comment("Data Catalog")` when configured (existing tests)

## 2. Docs and examples

- [x] 2.1 Mark the fields deprecated in their descriptions and in `docs/mappers/ckanext-dcat.md`
- [x] 2.2 Remove `catalog_name` / `catalog_url` from the SRADI entry in `dev_environment/config.all-rdis.yaml`

## 3. Follow-up

- [x] 3.1 Open the removal issue (#471) (prerequisites: SRADI `known_rdis` has `description` / `url`; deployed configs
      drop the keys) and link it from #461
