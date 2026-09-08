# Adopt Devinfra Wave A — Tasks

## 1. Pin and sync Wave A paths

- [ ] 1.1 Record Devinfra `main` commit SHA in the adopt PR description — pin:
      `906870bd18fa7fef3c5593f75440291e04ceb43e` (also in `proposal.md`)
- [ ] 1.2 Copy verbatim from that SHA: `docs/ai_review_policy.md`,
      `docs/surface-quality-bar.global.md`, `docs/review-fixer.md`,
      `docs/create-issue.md`, `docs/issue-fixer.md`
- [ ] 1.3 Copy verbatim: `.cursor/BUGBOT.md`,
      `.cursor/commands/{review,create,issue}-fixer.md`
- [ ] 1.4 Copy verbatim: `.github/copilot-instructions.md`,
      `.github/prompts/{review,create,issue}-fixer.prompt.md`
- [ ] 1.5 Copy verbatim: `.agents/skills/{review-fixer,create-issue,issue-fixer}/`
- [ ] 1.6 Diff local `.agents/skills/arctrl/` vs Devinfra; then copy verbatim
      first-party `.agents/skills/arctrl/` from Devinfra (replace local tree;
      preserve any unique tips in AGENTS if still needed)
- [ ] 1.7 Install/copy vendor skills `.agents/skills/{gh,docker,hadolint,uv}/`
      per Devinfra README (`gh skill install` or tree copy from SHA); do **not**
      remove `.agents/skills/config-wrapper/`
- [ ] 1.8 Copy verbatim: `scripts/ai/` (full tree including tests and lock) and
      `openspec/principles.global.md`

## 2. Thin Auth-B

- [ ] 2.1 Copy verbatim: `scripts/bin/gh`, `scripts/dev-tokens.sh`,
      `scripts/set-dev-tokens.sh`
- [ ] 2.2 Confirm `scripts/bin/git` and other Wave B paths are untouched

## 3. Local overlay (P3 + surface-bar) and cleanup

- [ ] 3.1 Create `openspec/principles.md` as P3 product overlay (extends
      `.global`; migrate product content from `openspec/specs/principles/spec.md`;
      no weakened Type Safety / Supported environment; **no** Finder/surface
      examples section)
- [ ] 3.2 Delete `openspec/specs/principles/`; update all references
      (`AGENTS.md`, `openspec/config.yaml`, and any other cites)
- [ ] 3.3 Create local `docs/surface-quality-bar.md` with the two product rows
      from `design.md` D5 (operator-facing contracts; source adapters + mapping
      internals); do not edit synced `.global.md` or policy for those rows
- [ ] 3.4 Update `AGENTS.md` pointers (`.global` + local principles; surface-bar
      global + local; vendor set; shared `arctrl`; keep `config-wrapper`;
      `m42-ai` / `scripts/ai`)
- [ ] 3.5 Extend minimal lint excludes (e.g. `.markdownlintignore`,
      `.prettierignore`, and any existing exclude patterns) for
      `docker` / `hadolint` / `uv` — no skeleton rewrite; do not treat
      first-party `arctrl` as a vendor exclude unless Devinfra does

## 4. Verify and smoke

- [ ] 4.1 Run `uv run --project scripts/ai m42-ai --help` and
      `uv run --project scripts/ai m42-ai auth-status` (re-prompt tokens via
      `source ./scripts/set-dev-tokens.sh` if needed)
- [ ] 4.2 Run `uv run --project scripts/ai pytest` for `scripts/ai` tests
- [ ] 4.3 Smoke `/review-fixer` against one real PR; briefly exercise
      `/create-issue` and `/issue-fixer` entrypoints
- [ ] 4.4 Diff synced paths against pinned SHA; confirm no intentional local
      edits on synced files (local overlay `docs/surface-quality-bar.md` and
      `openspec/principles.md` excepted)
- [ ] 4.5 Run `openspec validate --change adopt-devinfra-wave-a` (and repo
      `openspec validate --specs` if principles removal affects listing)
