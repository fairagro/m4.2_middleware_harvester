# Adopt Devinfra Wave C — Tasks

## 1. OpenSpec + branch

- [x] 1.1 Create change `adopt-devinfra-wave-c` (`skip_specs: true`)
- [x] 1.2 Branch `issue-169-adopt-devinfra-wave-c` from `main`

## 2. Bake product-app layout

- [x] 2.1 Copy `docker/Dockerfile.product-app.base` verbatim from Devinfra `main`
- [x] 2.2 Rewrite `docker/Dockerfile.harvester` as thin last stage (USER / CMD /
      HEALTHCHECK / runtime apk / labels only)
- [x] 2.3 Expand root `docker-bake.hcl` for `harvester-base` + `harvester` with
      `contexts` per Devinfra examples; keep CST target working
- [x] 2.4 Product-local healthcheck Bake path (`Dockerfile.harvester-healthcheck`)
      without editing synced base (golden rule)
- [x] 2.5 Smoke local Bake load using `versions.env` pins

## 3. CI callers → Devinfra

- [x] 3.1 Update `feature-pull-request.yml` to Devinfra `reusable-*@main`
- [x] 3.2 Update `pre-release.yml` and `release.yml` similarly
- [x] 3.3 Delete local `reusable-{code-quality,check,build,release}.yml`

## 4. Helm

- [x] 4.1 Switch `helm-pre-release.yml` / `helm-release.yml` to Devinfra
      `reusable-helm-*@main`
- [x] 4.2 Remove duplicated Helm job logic that now lives upstream

## 5. Docs / verify

- [x] 5.1 Devinfra follow-up for secondary binary:
      [m4.2_middleware_devinfra#71](https://github.com/fairagro/m4.2_middleware_devinfra/issues/71)
- [x] 5.2 `openspec validate --changes`
- [x] 5.3 Pause for user commit/push; draft PR with `Fixes #169`
