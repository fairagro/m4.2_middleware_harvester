# Product-local Bake targets for container-structure-test (shared CST runner).
# Full product-app Bake base adoption is Wave C; this keeps pre-push CST green.

target "harvester" {
  context    = "."
  dockerfile = "docker/Dockerfile.harvester"
  tags       = ["inspire-to-arc:test"]
}
