# Cursor devcontainer (DevPod)

Used by `scripts/start-devcontainer-cursor.sh` with DevPod + Cursor.

## Host bind mounts

| Mount | Source | Platforms |
| ----- | ------ | --------- |
| Git config | `${localEnv:HOME}${localEnv:USERPROFILE}/.gitconfig` → `~/.gitconfig-host` (read-only), copied to `~/.gitconfig` | Linux, macOS, Windows |
| SSH keys | `${localEnv:HOME}/.ssh` (read-only) | Linux, macOS, Windows |
| GitHub CLI auth | Docker volume `middleware-harvester-gh-config` → `~/.config/gh` | all |
| GPG agent + trustdb | `${localWorkspaceFolder}/.devcontainer/cursor/.host-gpg-cache` → `/host-gpg` | all |

`ensure-gpg-mounts.sh` runs via `initializeCommand` (and from `start-devcontainer-cursor.sh`).
Empty stub files are committed so the bind mount works even if the script cannot run.
On Linux with a running host GPG agent it hard-links the agent socket and copies
`trustdb.gpg`; otherwise stubs remain and container creation still succeeds.

`start-devcontainer-cursor.sh` creates an empty `~/.ssh` on the host if missing so the SSH
bind mount always succeeds.

## Git credentials (DevPod workaround)

The host `~/.gitconfig` is bind-mounted read-only at `~/.gitconfig-host`.
`scripts/setup-container-git.sh` copies it to writable `~/.gitconfig`, replaces
`credential.helper` with `!gh auth git-credential` (dropping DevPod's port 12049 agent),
and refreshes on every shell via `load-env.sh`.

**gh auth** is stored in a **container volume** (`~/.config/gh`), not on the host — a host
`~/.config/gh` directory is not required. Run once per DevPod machine (survives
`--recreate`):

```bash
gh auth login
```

## GPG agent forwarding (Linux only)

Host GPG files are exposed through a cache directory bind-mounted at `/host-gpg`.
`ensure-gpg-mounts.sh` prepares that directory before the container is created.

On Linux with systemd, ensure the host agent is running before recreate:

```bash
gpg -K
devpod up --recreate   # or reopen the devcontainer in Cursor
```

When no agent socket is available (macOS, Windows, or cloud hosts), stub files are
created so devcontainer creation succeeds. `setup-container-gpg.sh` skips agent
forwarding and prints a warning.

Host `~/.gitconfig` is mounted at `~/.gitconfig-host` and copied to `~/.gitconfig` on setup.
Git LFS filters are configured in the repository (`.git/config`) via `git lfs install --local` in `setup-git-lfs.sh`.

`scripts/setup-container-gpg.sh` (postCreate) symlinks the host agent socket to
`~/.gnupg/S.gpg-agent`, copies the host `trustdb.gpg` into a **writable** local file
(readonly bind mounts cannot be symlink targets for imports), and imports
`public_gpg_keys/*.asc`.

## One-time setup (postCreateCommand)

These run once per devcontainer create (not on every shell):

- `uv sync --dev --all-packages`
- `scripts/install-dev-hooks.sh` (pre-commit + Git LFS hooks)
- `scripts/setup-container-git.sh` (writable git config + optional host SSH)
- `scripts/setup-container-gpg.sh` (host agent + trustdb + public keys)

`scripts/load-env.sh` is sourced from `~/.bashrc` and only handles PATH, aliases, and
environment variables (including SOPS decryption when needed).

For a **local clone outside devcontainers**, run once after `uv sync`:

```bash
./scripts/install-dev-hooks.sh
./scripts/import-public-gpg-keys.sh
```

### macOS / Windows

This devcontainer variant does not support host GPG agent forwarding. Options:

1. **Decrypt secrets on the host** before starting the container (recommended):

   ```bash
   sops -d .env.integration.enc > .env
   ```

   `scripts/load-env.sh` skips SOPS decryption when `.env` already exists.

2. **Rely on stub mounts** — the container starts without host agent forwarding; decrypt
   `.env` on the host (option 1) or use `public_gpg_keys/` for encrypt-only workflows.

DevPod’s `--gpg-agent-forwarding` flag is not used here; it is a separate code path and
was found unreliable on some Linux hosts.
