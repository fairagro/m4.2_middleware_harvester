# Helm Harvester Chart

## Purpose

Defines how the harvester Helm chart turns values into the CronJob ConfigMap `config.yaml`, including optional
`rdi_catalog` map materialization into `config.repositories` for umbrella charts that cannot inject a computed list.

## Requirements

### Requirement: ConfigMap serialises harvester config YAML from chart values

The chart SHALL render a ConfigMap whose `config.yaml` data key is the YAML serialisation of the effective harvester
`config` object derived from chart values (including logging, API client, and repository list as applicable).

#### Scenario: List-only repositories still render

- **WHEN** `rdi_catalog` is absent, empty, or has no `enabled: true` entries, and `config.repositories` is a list
- **THEN** the ConfigMap `config.yaml` contains that repositories list under `repositories` without requiring
  `rdi_catalog` to be cleared

### Requirement: Optional rdi_catalog materialises config.repositories

When top-level `rdi_catalog` has at least one entry with `enabled: true`, the chart SHALL build `config.repositories` as
follows and SHALL use that list in the rendered `config.yaml`:

1. Include only entries whose `enabled` is true
2. Set each entry’s `rdi` field from the map key
3. Omit the `enabled` field from each rendered entry
4. Stable-sort entries by map key (deterministic ConfigMap output)
5. Preserve each entry’s remaining nested plugin fields (e.g. `inspire`, `generic`, `mapper`) as provided after Helm
   values merge

When no catalog entry is enabled, the chart SHALL leave `config.repositories` unchanged (including a hand-maintained
list alongside disabled catalog examples).

#### Scenario: Enabled catalog entries become the repositories list

- **WHEN** `rdi_catalog` defines `bonares` with `enabled: true` and plugin fields, and `publisso` with `enabled: false`
- **THEN** rendered `config.repositories` contains exactly one object with `rdi: bonares` and without an `enabled` field
- **AND** `publisso` is omitted

#### Scenario: Keys sort stably

- **WHEN** `rdi_catalog` enables both `zebra` and `alpha`
- **THEN** rendered `repositories` order is `alpha` then `zebra`

#### Scenario: Disabled-only catalog leaves the repositories list alone

- **WHEN** `rdi_catalog` has only `enabled: false` (or missing `enabled`) entries and `config.repositories` is a
  non-empty list
- **THEN** rendering succeeds and `repositories` stays the hand-maintained list

### Requirement: rdi_catalog and config.repositories are mutually exclusive when both active

When `rdi_catalog` has at least one `enabled: true` entry **and** `config.repositories` is a non-empty list, the chart
SHALL fail rendering (e.g. Helm `fail`) with a clear message that only one source of truth is allowed. An empty
repositories list with enabled catalog entries SHALL NOT fail for mutual exclusion; a disabled-only or absent/empty
catalog with a repositories list SHALL NOT fail.

#### Scenario: Both sources set fails at template time

- **WHEN** values enable at least one `rdi_catalog` entry and set a non-empty `config.repositories`
- **THEN** `helm template` / install fails before producing a ConfigMap

#### Scenario: Catalog alone succeeds

- **WHEN** values enable at least one `rdi_catalog` entry and `config.repositories` is absent or empty
- **THEN** rendering succeeds and repositories come from the catalog

### Requirement: Chart documents rdi_catalog for operators

The chart `values.yaml` SHALL document the `rdi_catalog` map shape (per-RDI `enabled` plus plugin nested keys) and the
mutual-exclusion rule with `config.repositories` (fail when any catalog entry is enabled and the list is non-empty).

#### Scenario: values.yaml mentions rdi_catalog

- **WHEN** an operator reads the chart default values comments
- **THEN** `rdi_catalog` and the fail-both rule are described
