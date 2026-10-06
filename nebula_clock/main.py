#!/usr/bin/env python3
"""Nebula Clock v2 — customizable terminal rice utility centered around a clock."""
from __future__ import annotations

import argparse
import curses
import locale
import os
import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):
    # Allows `python3 nebula_clock/main.py` when running from the repository.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nebula_clock.config import (
        BUILTIN_THEME_DIR,
        USER_CONFIG,
        detect_theme,
        load_config,
        load_json,
        save_default_config,
    )
    from nebula_clock.render import draw_text, run
else:
    from .config import BUILTIN_THEME_DIR, USER_CONFIG, detect_theme, load_config, load_json, save_default_config
    from .render import draw_text, run


def list_themes() -> int:
    paths = sorted(BUILTIN_THEME_DIR.glob("*.json"))
    for path in paths:
        data = load_json(path)
        print(f"{path.stem:22} {data.get('badge', ''):8} {data.get('description', '')}")
    print(f"\n{len(paths)} built-in themes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configurable animated terminal clock and rice utility"
    )
    parser.add_argument("--theme", help="built-in theme name")
    parser.add_argument("--config", type=Path, help="path to a JSON config file")
    parser.add_argument("--list-themes", action="store_true", help="list built-in themes")
    parser.add_argument("--print-theme", action="store_true", help="print the automatically detected theme")
    parser.add_argument("--init-config", action="store_true", help="create ~/.config/nebula-clock/config.json")
    parser.add_argument("--no-seconds", action="store_true", help="hide seconds")
    parser.add_argument("--no-stars", action="store_true", help="disable stars")
    parser.add_argument("--clock-box", action="store_true", help="enable Clock Box")
    parser.add_argument("--fetch", action="store_true", help="enable Mini Fetch")
    parser.add_argument("--fetch-box", action="store_true", help="enable Mini Fetch with a box")
    parser.add_argument("--logo", help="enable a logo; use 'auto', a theme name, or 'custom'")
    parser.add_argument("--font", choices=("digital", "block", "ascii", "dot", "thin"), help="clock font style")
    parser.add_argument("--once", action="store_true", help="print one frame and exit")
    args = parser.parse_args()

    if args.list_themes:
        return list_themes()
    if args.print_theme:
        print(detect_theme())
        return 0
    if args.init_config:
        save_default_config(USER_CONFIG)
        print(f"Created {USER_CONFIG}")
        return 0

    locale.setlocale(locale.LC_ALL, "")
    config = load_config(args.config, args.theme)

    if args.no_seconds:
        config["display"]["show_seconds"] = False
    if args.no_stars:
        config["animation"]["stars"] = False
    if args.clock_box:
        config["clock_box"]["enabled"] = True
    if args.fetch or args.fetch_box:
        config["fetch"]["enabled"] = True
    if args.fetch_box:
        config["fetch"]["box"] = True
    if args.logo is not None:
        config["logo"]["enabled"] = True
        config["logo"]["source"] = args.logo
    if args.font:
        config["display"]["font"] = args.font

    size = shutil.get_terminal_size((80, 24))
    if args.once:
        print(draw_text(size.lines, size.columns, config))
        return 0

    os.environ.setdefault("ESCDELAY", "25")
    try:
        curses.wrapper(run, config, args)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
