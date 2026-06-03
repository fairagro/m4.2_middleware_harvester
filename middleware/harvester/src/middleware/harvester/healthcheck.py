"""Liveness health check for the Middleware Harvester.

Exits 0 if the heartbeat file exists and was touched within *max_age* seconds.
Exits 1 otherwise (file absent or stale).

Designed to be compiled into a standalone binary via PyInstaller and called
directly by the Kubernetes liveness probe — no shell required.
"""

import argparse
import os
import time

_DEFAULT_MAX_AGE = 300  # 5 minutes — covers 10× the default 30 s heartbeat interval


def _check(path: str, max_age: int) -> bool:
    """Return True if *path* exists and its mtime is within *max_age* seconds."""
    try:
        age = time.time() - os.stat(path).st_mtime
    except OSError:
        return False
    return age < max_age


def main() -> int:
    """Parse arguments and run the liveness check."""
    parser = argparse.ArgumentParser(description="Harvester liveness check.")
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the heartbeat file written by the harvester.",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=_DEFAULT_MAX_AGE,
        help="Maximum accepted file age in seconds (default: %(default)s).",
    )
    args = parser.parse_args()
    return 0 if _check(args.path, args.max_age) else 1


if __name__ == "__main__":
    raise SystemExit(main())
