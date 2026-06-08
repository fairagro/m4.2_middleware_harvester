# Cursor devcontainer (DevPod)

Used by `scripts/start-devcontainer-cursor.sh` with DevPod + Cursor.

## Host bind mounts

| Mount | Source | Platforms |
| ----- | ------ | --------- |
| Git config | `${localEnv:HOME}${localEnv:USERPROFILE}/.gitconfig` | Linux, macOS, Windows |
| GPG agent socket | `${localEnv:XDG_RUNTIME_DIR}/gnupg/S.gpg-agent.extra` | **Linux only** |
| GPG trustdb | `${localEnv:HOME}/.gnupg/trustdb.gpg` | Linux, macOS, Windows (optional file) |

## GPG agent forwarding (Linux only)

The GPG agent bind mount relies on `XDG_RUNTIME_DIR`, which systemd sets on Linux
(typically `/run/user/<uid>`). It is usually **not** set on macOS or Windows.

If `XDG_RUNTIME_DIR` is empty, the mount source resolves to `/gnupg/S.gpg-agent.extra`,
which does not exist, and **devcontainer creation fails**.

### Linux

Before `devpod up --recreate`, ensure the host agent is running:

```bash
gpg -K
```

`postCreateCommand` symlinks the mounted socket to `~/.gnupg/S.gpg-agent` so `gpg` and
`sops` inside the container use the host agent.

### macOS / Windows

This devcontainer variant does not support host GPG agent forwarding. Options:

1. **Decrypt secrets on the host** before starting the container (recommended):

   ```bash
   sops -d .env.integration.enc > .env
   ```

   `scripts/load-env.sh` skips SOPS decryption when `.env` already exists.

2. **Remove the GPG-related `mounts` entries** from `devcontainer.json` (and rely on
   option 1 or on `public_gpg_keys/` for encrypt-only workflows).

DevPod’s `--gpg-agent-forwarding` flag is not used here; it is a separate code path and
was found unreliable on some Linux hosts.
