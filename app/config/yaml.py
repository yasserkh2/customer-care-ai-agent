from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_yaml_config(
    config_path: str | Path = "config.yml",
    *,
    overwrite: bool = False,
    protected_keys: set[str] | None = None,
) -> None:
    path = Path(config_path)
    if not path.exists():
        return

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return

    for key, value in _flatten_mapping(payload).items():
        _set_env_var(
            key=key,
            value=value,
            overwrite=overwrite,
            protected_keys=protected_keys,
        )


def _flatten_mapping(
    payload: dict[str, Any],
    prefix: tuple[str, ...] = (),
) -> dict[str, str]:
    flattened: dict[str, str] = {}
    for raw_key, raw_value in payload.items():
        key = str(raw_key).strip()
        if not key:
            continue

        next_prefix = prefix + (key,)
        if isinstance(raw_value, dict):
            flattened.update(_flatten_mapping(raw_value, prefix=next_prefix))
            continue

        env_key = "_".join(_normalize_env_segment(part) for part in next_prefix)
        env_value = _normalize_env_value(raw_value)
        if env_key and env_value is not None:
            flattened[env_key] = env_value
    return flattened


def _normalize_env_segment(value: str) -> str:
    normalized = value.strip().replace("-", "_").replace(" ", "_")
    return normalized.upper()


def _normalize_env_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        normalized = value.strip()
        return normalized if normalized else None
    return str(value)


def _set_env_var(
    *,
    key: str,
    value: str,
    overwrite: bool,
    protected_keys: set[str] | None,
) -> None:
    if not key:
        return
    if protected_keys and key in protected_keys:
        return
    if not overwrite and key in os.environ:
        return
    os.environ[key] = value
