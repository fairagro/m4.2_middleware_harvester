# Product-local Buildx Bake file (NOT synced). Target name must match
# reusable-build `components` matrix entry ("harvester").
#
# Version pins: do NOT default PYTHON_VERSION / UV_VERSION / PIP_VERSION /
# ALPINE_* / PYINSTALLER_VERSION here — inject from versions.env (reusable-build
# and scripts/run-container-structure-test.sh do this).
#
# Healthcheck: secondary product-local target (synced base is single-binary).
# Prefer a generic Devinfra secondary-binary feature when upstream lands.

variable "APP_VERSION" {
  default = "0.0.0"
}

variable "PYTHON_VERSION" {}
variable "ALPINE_VERSION" {}
variable "ALPINE_MINOR" {}
variable "PIP_VERSION" {}
variable "UV_VERSION" {}
variable "PYINSTALLER_VERSION" {}

variable "IMAGE_TAG" {
  default = "inspire-to-arc:test"
}

target "harvester-wheels" {
  context    = "."
  dockerfile = "docker/Dockerfile.product-app.base"
  target     = "package-builder"
  args = {
    APP_VERSION       = APP_VERSION
    PYTHON_VERSION    = PYTHON_VERSION
    ALPINE_MINOR      = ALPINE_MINOR
    PIP_VERSION       = PIP_VERSION
    UV_VERSION        = UV_VERSION
    UV_BUILD_PACKAGES = "inspire harvester linked_data"
  }
}

target "harvester-healthcheck" {
  context    = "."
  dockerfile = "docker/Dockerfile.harvester-healthcheck"
  target     = "export-healthcheck"
  contexts = {
    wheels = "target:harvester-wheels"
  }
  args = {
    APP_VERSION         = APP_VERSION
    PYTHON_VERSION      = PYTHON_VERSION
    ALPINE_MINOR        = ALPINE_MINOR
    PIP_VERSION         = PIP_VERSION
    UV_VERSION          = UV_VERSION
    PYINSTALLER_VERSION = PYINSTALLER_VERSION
  }
}

target "harvester-base" {
  context    = "."
  dockerfile = "docker/Dockerfile.product-app.base"
  target     = "export-binaries"
  args = {
    APP_VERSION         = APP_VERSION
    PYTHON_VERSION      = PYTHON_VERSION
    ALPINE_MINOR        = ALPINE_MINOR
    PIP_VERSION         = PIP_VERSION
    UV_VERSION          = UV_VERSION
    PYINSTALLER_VERSION = PYINSTALLER_VERSION
    UV_BUILD_PACKAGES   = "inspire harvester linked_data"
    BINARY_NAME         = "harvester"
    PYINSTALLER_IMPORT  = "middleware.harvester"
    EXTRA_PYINSTALLER_ARGS = "--copy-metadata harvester --copy-metadata inspire --copy-metadata fairagro-middleware-api-client --copy-metadata fairagro-middleware-shared"
  }
}

target "harvester" {
  context    = "."
  dockerfile = "docker/Dockerfile.harvester"
  contexts = {
    export_bins       = "target:harvester-base"
    healthcheck_bins  = "target:harvester-healthcheck"
  }
  args = {
    ALPINE_VERSION = ALPINE_VERSION
    BINARY_NAME    = "harvester"
    RUNTIME_USER   = "harvester"
  }
  tags      = [IMAGE_TAG]
  platforms = ["linux/amd64"]
}
