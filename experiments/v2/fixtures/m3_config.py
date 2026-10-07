import json
import os
from pathlib import Path

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
    "workers": 4,
    "allowed_origins": [],
}


def _coerce(value: str, like):
    """Convert an environment string to the type of the default value."""
    if isinstance(like, bool):
        return bool(value)
    if isinstance(like, int):
        return int(value)
    if isinstance(like, list):
        return [v.strip() for v in value.split(",") if v.strip()]
    return value


def load_config(path: str = None, env_prefix: str = "APP_") -> dict:
    config = DEFAULTS
    if path:
        p = Path(path)
        if p.exists():
            with p.open() as f:
                config.update(json.load(f))
    for key, default in DEFAULTS.items():
        env_key = env_prefix + key.upper()
        if env_key in os.environ:
            config[key] = _coerce(os.environ[env_key], default)
    validate(config)
    return config


def validate(config: dict) -> None:
    unknown = set(config) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"unknown config keys: {sorted(unknown)}")
    if not (0 < config["port"] < 65536):
        raise ValueError("port out of range")
    if config["workers"] < 1:
        raise ValueError("workers must be at least 1")


def dump_config(config: dict, path: str) -> None:
    tmp = Path(path).with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(config, f, indent=2, sort_keys=True)
    os.replace(tmp, path)
