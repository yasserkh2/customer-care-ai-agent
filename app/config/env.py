from __future__ import annotations

import os
from pathlib import Path

from app.config.yaml import load_yaml_config


def load_env_file(
    env_path: str | Path = ".env",
    *,
    overwrite: bool = False,
    protected_keys: set[str] | None = None,
) -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue
        if protected_keys and key in protected_keys:
            continue
        if not overwrite and key in os.environ:
            continue

        os.environ[key] = value


def load_runtime_config(
    config_path: str | Path = "config.yml",
    env_path: str | Path = ".env",
) -> None:
    original_env_keys = set(os.environ)
    load_yaml_config(
        config_path,
        overwrite=False,
        protected_keys=original_env_keys,
    )
    load_env_file(
        env_path,
        overwrite=True,
        protected_keys=original_env_keys,
    )
