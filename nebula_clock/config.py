from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

APP_NAME = "nebula-clock"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
USER_CONFIG = CONFIG_DIR / "config.json"
BUILTIN_THEME_DIR = Path(__file__).with_name("themes")

DEFAULT_CONFIG = {
    "theme": "auto",
    "display": {
        "show_seconds": True,
        "show_date": True,
        "show_title": True,
        "scale": "auto",
        "font": "digital",
        "block": "█",
        "fallback_block": "#",
    },
    "logo": {
        "enabled": False,
        "source": "auto",
        "position": "right",
        "custom": "",
    },
    "fetch": {
        "enabled": False,
        "box": False,
        "position": "left",
    },
    "clock_box": {
        "enabled": False,
        "style": "rounded",
    },
    "custom_text": {
        "enabled": False,
        "text": "",
        "position": "bottom",
    },
    "colors": {},
    "animation": {
        "stars": True,
        "star_density": 1.0,
        "star_speed": 1.0,
        "star_life_min": 14,
        "star_life_max": 45,
        "logo": {
            "enabled": False,
            "type": "fade",
            "interval": 6.0,
            "duration": 2.5,
        },
        "custom_text": {
            "enabled": False,
            "type": "fade",
            "interval": 8.0,
            "duration": 2.5,
        },
    },
}

THEME_ALIASES = {
    "linuxmint": "mint",
    "pop": "pop_os",
    "popos": "pop_os",
    "opensuse-leap": "opensuse",
    "opensuse-tumbleweed": "opensuse",
    "redhat": "rhel",
}

FEDORA_VARIANT_MAP = {
    "silverblue": "fedora-silverblue",
    "kinoite": "fedora-kinoite",
    "sericea": "fedora-sericea",
    "onyx": "fedora-onyx",
}


def deep_merge(base: dict, override: dict) -> dict:
    """Merge nested dictionaries without changing the original inputs."""
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _read_os_release() -> dict[str, str]:
    data: dict[str, str] = {}
    path = Path("/etc/os-release")
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            data[key] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return data


def _theme_exists(name: str) -> bool:
    return (BUILTIN_THEME_DIR / f"{name}.json").exists()


def detect_theme() -> str:
    """Choose the best matching built-in theme from /etc/os-release."""
    data = _read_os_release()
    variant = data.get("VARIANT_ID", "").lower().replace("_", "-")
    candidate = FEDORA_VARIANT_MAP.get(variant)
    if candidate and _theme_exists(candidate):
        return candidate

    candidates = []
    for key in ("ID", "VARIANT_ID"):
        value = data.get(key, "").lower().replace("_", "-")
        if value:
            candidates.append(value)

    for value in candidates:
        candidate = THEME_ALIASES.get(value, value)
        if _theme_exists(candidate):
            return candidate

    for value in data.get("ID_LIKE", "").lower().split():
        value = value.replace("_", "-")
        candidate = THEME_ALIASES.get(value, value)
        if _theme_exists(candidate):
            return candidate

    return "ubuntu" if _theme_exists("ubuntu") else sorted(
        p.stem for p in BUILTIN_THEME_DIR.glob("*.json")
    )[0]


def load_theme(name: str) -> dict:
    theme_path = BUILTIN_THEME_DIR / f"{name}.json"
    if not theme_path.exists():
        raise SystemExit(f"Unknown theme: {name}. Use --list-themes to see available themes.")
    return load_json(theme_path)


def load_config(path: Path | None = None, theme_override: str | None = None) -> dict:
    """Load defaults, the user's config, an optional config, and then a theme."""
    config = deepcopy(DEFAULT_CONFIG)

    if USER_CONFIG.exists():
        config = deep_merge(config, load_json(USER_CONFIG))

    if path and path.exists():
        config = deep_merge(config, load_json(path))

    requested_theme = theme_override or config.get("theme", "auto")
    theme_name = detect_theme() if requested_theme in (None, "auto") else requested_theme
    theme = load_theme(theme_name)

    # Theme values stay as defaults; explicit user colors override them.
    user_colors = config.get("colors", {})
    config["colors"] = deep_merge(theme, user_colors)
    config["theme"] = theme_name
    return config


def save_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit(f"Config already exists: {path}")
    path.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_example(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
