# Dev Container (Cursor / VS Code)

Open with **Dev Containers: Reopen in Container**. Config:

- [`.devcontainer/devcontainer.json`](devcontainer.json)

Uses [`.devcontainer/Dockerfile`](Dockerfile) with Docker-in-Docker.
Includes Node.js and the [OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI (`openspec`) for spec-driven development.

## What the Dev Containers extension provides

Git credentials, SSH agent forwarding, and GPG keys are handled by the
[Dev Containers extension](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials)
— no custom bind mounts required.

Ensure on the **host**:

- `git config --global user.name` / `user.email` are set
- SSH agent is running with your keys loaded (`ssh-add`) for SSH remotes
- GPG agent is running for SOPS decryption and commit signing (`gpg -K`)

## gh auth (HTTPS Git)

`gh auth login` credentials are stored in a Docker volume (`middleware-harvester-gh-config`)
so they survive container rebuilds. Run once per machine:

```bash
gh auth login
```

## One-time setup (postCreateCommand)

Runs once per devcontainer create:

- `uv sync --dev --all-packages`
- `scripts/install-dev-hooks.sh` (pre-commit + Git LFS hooks)
- `scripts/import-public-gpg-keys.sh` (project public GPG keys for SOPS)

`scripts/load-env.sh` is sourced from `~/.bashrc` on each shell and handles PATH,
aliases, ggshield status, and SOPS `.env` decryption.

Cursor Source Control (≥3.15.6) may force `core.hooksPath=/dev/null` and skip
pre-commit. `remoteEnv.PATH` prepends `scripts/bin` so SCM `git` runs
`scripts/cursor-git.sh`, which strips that pin ([forum #167719](https://forum.cursor.com/t/167719)).
Rebuild/reopen the container after pulling this change so `remoteEnv` applies.

For a **local clone outside devcontainers**, run once after `uv sync`:

```bash
./scripts/install-dev-hooks.sh
./scripts/import-public-gpg-keys.sh
```

## macOS / Windows

GPG agent forwarding can be unreliable depending on the host OS and IDE version.
If `sops -d .env.integration.enc` fails inside the container, decrypt on the host:

```bash
sops -d .env.integration.enc > .env
```

`scripts/load-env.sh` skips SOPS decryption when `.env` already exists.
