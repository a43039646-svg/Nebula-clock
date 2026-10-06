from __future__ import annotations

import curses
import locale
import time
from .effects import Sky, animation_state
from .fetch import collect
from .logos import get_logo, get_logo_fallback

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

FONT_SETS = {
    "digital": {
        "0": ["┌──┐", "│  │", "│  │", "│  │", "└──┘"],
        "1": ["  ┐ ", "  │ ", "  │ ", "  │ ", "──┴─"],
        "2": ["┌──┐", "   │", "┌──┘", "│   ", "└──┘"],
        "3": ["┌──┐", "   │", " ──┤", "   │", "└──┘"],
        "4": ["│  │", "│  │", "└──┤", "   │", "   │"],
        "5": ["┌──┐", "│   ", "└──┐", "   │", "└──┘"],
        "6": ["┌──┐", "│   ", "├──┐", "│  │", "└──┘"],
        "7": ["┌──┐", "   │", "   │", "   │", "   │"],
        "8": ["┌──┐", "│  │", "├──┤", "│  │", "└──┘"],
        "9": ["┌──┐", "│  │", "└──┤", "   │", "└──┘"],
        ":": [" ", "·", " ", "·", " "],
    },
    "block": {
        "0": ["███", "█ █", "█ █", "█ █", "███"], "1": [" █ ", "██ ", " █ ", " █ ", "███"],
        "2": ["███", "  █", "███", "█  ", "███"], "3": ["███", "  █", "███", "  █", "███"],
        "4": ["█ █", "█ █", "███", "  █", "  █"], "5": ["███", "█  ", "███", "  █", "███"],
        "6": ["███", "█  ", "███", "█ █", "███"], "7": ["███", "  █", "  █", "  █", "  █"],
        "8": ["███", "█ █", "███", "█ █", "███"], "9": ["███", "█ █", "███", "  █", "███"],
        ":": [" ", "█", " ", "█", " "],
    },
    "ascii": {
        "0": ["###", "# #", "# #", "# #", "###"], "1": [" # ", "## ", " # ", " # ", "###"],
        "2": ["###", "  #", "###", "#  ", "###"], "3": ["###", "  #", "###", "  #", "###"],
        "4": ["# #", "# #", "###", "  #", "  #"], "5": ["###", "#  ", "###", "  #", "###"],
        "6": ["###", "#  ", "###", "# #", "###"], "7": ["###", "  #", "  #", "  #", "  #"],
        "8": ["###", "# #", "###", "# #", "###"], "9": ["###", "# #", "###", "  #", "###"],
        ":": [" ", "#", " ", "#", " "],
    },
    "dot": {
        "0": ["●●●", "● ●", "● ●", "● ●", "●●●"], "1": [" ● ", "●● ", " ● ", " ● ", "●●●"],
        "2": ["●●●", "  ●", "●●●", "●  ", "●●●"], "3": ["●●●", "  ●", "●●●", "  ●", "●●●"],
        "4": ["● ●", "● ●", "●●●", "  ●", "  ●"], "5": ["●●●", "●  ", "●●●", "  ●", "●●●"],
        "6": ["●●●", "●  ", "●●●", "● ●", "●●●"], "7": ["●●●", "  ●", "  ●", "  ●", "  ●"],
        "8": ["●●●", "● ●", "●●●", "● ●", "●●●"], "9": ["●●●", "● ●", "●●●", "  ●", "●●●"],
        ":": [" ", "●", " ", "●", " "],
    },
    "thin": {
        "0": ["───", "│ │", "│ │", "│ │", "───"], "1": [" │ ", "╱│ ", " │ ", " │ ", "─┴─"],
        "2": ["───", "  │", "───", "│  ", "───"], "3": ["───", "  │", "───", "  │", "───"],
        "4": ["│ │", "│ │", "───", "  │", "  │"], "5": ["───", "│  ", "───", "  │", "───"],
        "6": ["───", "│  ", "───", "│ │", "───"], "7": ["───", "  │", "  │", "  │", "  │"],
        "8": ["───", "│ │", "───", "│ │", "───"], "9": ["───", "│ │", "───", "  │", "───"],
        ":": [" ", "·", " ", "·", " "],
    },
}

BOXES = {
    "single": ("┌", "─", "┐", "│", "└", "┘"),
    "double": ("╔", "═", "╗", "║", "╚", "╝"),
    "rounded": ("╭", "─", "╮", "│", "╰", "╯"),
    "ascii": ("+", "-", "+", "|", "+", "+"),
}

ANSI8 = {"black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4, "magenta": 5, "cyan": 6, "white": 7}


def utf8_ok() -> bool:
    try:
        return "utf" in locale.nl_langinfo(locale.CODESET).lower()
    except AttributeError:
        return True


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _xterm_palette() -> list[tuple[int, int, int]]:
    palette = [
        (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128), (128, 0, 128),
        (0, 128, 128), (192, 192, 192), (128, 128, 128), (255, 0, 0), (0, 255, 0),
        (255, 255, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255),
    ]
    levels = [0, 95, 135, 175, 215, 255]
    palette += [(r, g, b) for r in levels for g in levels for b in levels]
    palette += [(v, v, v) for v in range(8, 248, 10)]
    return palette


XTERM = _xterm_palette()


def rgb_to_xterm(value: str) -> int:
    if value.lower() in ANSI8:
        return ANSI8[value.lower()]
    target = hex_to_rgb(value)
    return min(range(len(XTERM)), key=lambda i: sum((XTERM[i][j] - target[j]) ** 2 for j in range(3)))


def palette_color(value: str | None, fallback: str, use_256: bool) -> int:
    value = value or fallback
    try:
        return rgb_to_xterm(value) if use_256 else ANSI8.get(value.lower(), 7)
    except (ValueError, AttributeError):
        return rgb_to_xterm(fallback) if use_256 else ANSI8.get(fallback.lower(), 7)


def clock_rows(now, seconds: bool, scale: int, colon_on: bool, config: dict) -> list[str]:
    font_name = str(config["display"].get("font", "digital")).lower()
    font = FONT_SETS.get(font_name, FONT_SETS["block"])
    block = config["display"].get("block", "█") if utf8_ok() else config["display"].get("fallback_block", "#")
    text = time.strftime("%H:%M:%S" if seconds else "%H:%M", now)
    font_height = len(font["0"])
    rows = [""] * font_height
    for index, char in enumerate(text):
        glyph = [" "] * font_height if char == ":" and not colon_on else font[char]
        for row in range(font_height):
            piece = glyph[row]
            if font_name == "block":
                piece = piece.replace("█", block)
            if scale == 2:
                piece = "".join(char * 2 for char in piece)
            rows[row] += piece + (" " * scale if index < len(text) - 1 else "")
    return rows


def clock_size(seconds: bool, scale: int, config: dict) -> tuple[int, int]:
    rows = clock_rows(time.localtime(), seconds, scale, True, config)
    return len(rows[0]), len(rows)


def layout(rows: int, cols: int, seconds: bool, scale_mode: str, config: dict) -> tuple[int, int, int, int, tuple[int, int, int, int]]:
    if scale_mode == "2":
        scale = 2
    elif scale_mode == "1":
        scale = 1
    else:
        side_panels = bool(config.get("fetch", {}).get("enabled")) or bool(config.get("logo", {}).get("enabled"))
        test_width = clock_size(seconds, 2, config)[0]
        if side_panels and cols < 100:
            scale = 1
        else:
            scale = 2 if cols >= test_width + 10 else 1

    width, height = clock_size(seconds, scale, config)

    left_reserved = 0
    right_reserved = 0
    fetch = config.get("fetch", {})
    logo = config.get("logo", {})
    if fetch.get("enabled"):
        if fetch.get("position", "left") == "right":
            right_reserved += min(34, max(24, cols // 3)) + 5
        else:
            left_reserved += min(34, max(24, cols // 3)) + 5
    if logo.get("enabled"):
        if logo.get("position", "right") == "left":
            left_reserved += 10
        else:
            right_reserved += 10

    available_left = left_reserved
    available_right = max(available_left, cols - right_reserved)
    available_width = max(1, available_right - available_left)

    if width + 2 > available_width and scale == 2 and scale_mode == "auto":
        scale = 1
        width, height = clock_size(seconds, scale, config)
    left = available_left + max(0, (available_width - width) // 2)
    left = min(left, max(0, cols - width - 1))
    top = max(1, (rows - 10) // 2)
    return scale, width, top, left, (top - 1, top + height, left - 3, left + width + 3)


def add_text(cells: dict, y: int, x: int, text: str, color: str, bold: bool = False) -> None:
    for offset, char in enumerate(text):
        if char != " ":
            cells[(y, x + offset)] = (char, color, bold)


def add_box(cells: dict, top: int, left: int, bottom: int, right: int, style: str, color: str) -> None:
    chars = BOXES.get(style, BOXES["rounded"])
    tl, h, tr, v, bl, br = chars
    if right <= left or bottom <= top:
        return
    add_text(cells, top, left, tl + h * max(0, right - left - 1) + tr, color, False)
    for y in range(top + 1, bottom):
        add_text(cells, y, left, v, color, False)
        add_text(cells, y, right, v, color, False)
    add_text(cells, bottom, left, bl + h * max(0, right - left - 1) + br, color, False)


def centered_start(cols: int, width: int) -> int:
    return max(0, (cols - width) // 2)


def logo_text(config: dict, theme_name: str, theme: dict) -> str:
    custom = str(config["logo"].get("custom", ""))
    source = str(config["logo"].get("source", "auto"))
    name = theme_name if source in ("auto", "theme") else source
    if source == "custom":
        return custom or "LINUX"
    return get_logo(name, custom)


def logo_fallback(config: dict, theme_name: str) -> str:
    source = str(config["logo"].get("source", "auto"))
    name = theme_name if source in ("auto", "theme") else source
    return get_logo_fallback(name, str(config["logo"].get("custom", "")))


def render_logo(cells: dict, rows: int, cols: int, config: dict, theme_name: str, theme: dict, now: float, color: str) -> None:
    if not config["logo"].get("enabled", False):
        return
    text = logo_text(config, theme_name, theme) if utf8_ok() else logo_fallback(config, theme_name)
    position = str(config["logo"].get("position", "right"))
    anim = config["animation"].get("logo", {})
    kind = anim.get("type", "none") if anim.get("enabled", False) else "none"
    visible, strength, offset = animation_state(kind, now, anim.get("interval", 6), anim.get("duration", 2.5))
    if not visible:
        return
    display_color = strength if strength in {"dim", "mid", "bright"} else color
    y = max(1, rows // 2 - 1)
    width = len(text)
    if position == "left":
        x = max(0, centered_start(cols, width) - 18 - offset)
    else:
        x = min(max(0, cols - width), centered_start(cols, width) + 18 + offset)
    add_text(cells, y, x, text, display_color if display_color != "bright" else color, True)


def render_fetch(cells: dict, rows: int, cols: int, config: dict, theme_name: str, now: float, color: str, box_color: str) -> None:
    settings = config["fetch"]
    if not settings.get("enabled", False):
        return
    items = collect(theme_name)
    max_width = max(20, min(32, cols // 3))

    def clip(value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return value[: max(0, limit - 1)] + "…"

    lines = [f"{key:<6} {clip(value, max_width - 7)}" for key, value in items]
    width = min(max((len(line) for line in lines), default=0), max_width)
    lines = [clip(line, width) for line in lines]
    height = len(lines)
    y = max(1, (rows - height) // 2)
    position = settings.get("position", "left")
    if position == "right":
        x = max(0, cols - width - 3)
    else:
        x = 2
    if settings.get("box", False):
        add_box(cells, y - 1, x - 1, y + height, x + width, "rounded", box_color)
    for i, line in enumerate(lines):
        add_text(cells, y + i, x, line, color, False)


def render_custom_text(cells: dict, rows: int, cols: int, config: dict, now: float, color: str) -> None:
    settings = config["custom_text"]
    if not settings.get("enabled", False):
        return
    raw = settings.get("text", "")
    lines = raw if isinstance(raw, list) else str(raw).splitlines()
    lines = [str(line) for line in lines if str(line)]
    if not lines:
        return
    anim = config["animation"].get("custom_text", {})
    kind = anim.get("type", "none") if anim.get("enabled", False) else "none"
    visible, strength, offset = animation_state(kind, now, anim.get("interval", 8), anim.get("duration", 2.5))
    if not visible:
        return
    y_start = max(0, rows - len(lines) - 1)
    for i, line in enumerate(lines):
        x = centered_start(cols, len(line)) + offset
        add_text(cells, y_start + i, x, line, strength if strength in {"dim", "mid", "bright"} else color, False)


def build_cells(rows: int, cols: int, now_struct, sky: Sky | None, config: dict, theme_name: str) -> dict:
    cells = {}
    display = config["display"]
    colors = config["colors"]
    seconds = bool(display.get("show_seconds", True))
    scale, width, top, left, _ = layout(rows, cols, seconds, display.get("scale", "auto"), config)
    colon_on = int(time.time() * 2) % 2 == 0 or not seconds

    if sky:
        for star in sky.stars:
            char, color = star.look()
            cells[(star.y, star.x)] = (char, color, color == "bright")

    digits = clock_rows(now_struct, seconds, scale, colon_on, config)
    for row, line in enumerate(digits):
        add_text(cells, top + row, left, line, "digit", True)

    if config.get("clock_box", {}).get("enabled", False):
        add_box(cells, top - 1, left - 2, top + len(digits), left + width + 1,
                config["clock_box"].get("style", "rounded"), "box")

    next_row = top + len(digits) + 1
    if display.get("show_date", True):
        date = f"{DAYS[now_struct.tm_wday]} {now_struct.tm_mday:02d} {MONTHS[now_struct.tm_mon - 1]} {now_struct.tm_year}"
        add_text(cells, next_row, centered_start(cols, len(date)), date, "date", False)

    if display.get("show_title", True):
        title = str(colors.get("title_text", "L I N U X   C L O C K"))
        badge = str(colors.get("badge", "LIN"))[:8]
        add_text(cells, top + len(digits) + 3, centered_start(cols, len(title)), title, "title", False)
        badge_text = f"[ {badge} ]"
        add_text(cells, top + len(digits) + 4, centered_start(cols, len(badge_text)), badge_text, "title", True)

    render_logo(cells, rows, cols, config, theme_name, colors, time.monotonic(), "logo")
    render_fetch(cells, rows, cols, config, theme_name, time.monotonic(), "fetch", "box")
    render_custom_text(cells, rows, cols, config, time.monotonic(), "custom")
    return cells


def color_map(config: dict) -> dict[str, str]:
    colors = config["colors"]
    return {
        "digit": colors.get("clock") or colors.get("digit") or "#ffffff",
        "date": colors.get("date") or "#ffffff",
        "title": colors.get("title") or "#ffffff",
        "dim": colors.get("dim") or "#666666",
        "mid": colors.get("mid") or colors.get("digit") or "#aaaaaa",
        "bright": colors.get("bright") or "#ffffff",
        "box": colors.get("box") or colors.get("title") or "#ffffff",
        "logo": colors.get("logo") or colors.get("title") or "#ffffff",
        "fetch": colors.get("fetch") or colors.get("date") or "#ffffff",
        "custom": colors.get("custom_text") or colors.get("title") or "#ffffff",
    }


def make_pairs(stdscr, config: dict) -> dict[str, int]:
    try:
        curses.start_color()
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK
    use_256 = curses.COLORS >= 256
    mapping = color_map(config)
    pairs = {}
    for index, name in enumerate(mapping, start=1):
        value = mapping[name]
        number = palette_color(value, "#ffffff", use_256)
        curses.init_pair(index, number, bg)
        pairs[name] = curses.color_pair(index)
    return pairs


def draw_text(rows: int, cols: int, config: dict) -> str:
    display = config["display"]
    box = layout(rows, cols, bool(display.get("show_seconds", True)), display.get("scale", "auto"), config)[4]
    sky = Sky(rows, cols, box, config["animation"], enabled=bool(config["animation"].get("stars", True)))
    for _ in range(20):
        sky.tick()
    cells = build_cells(rows, cols, time.localtime(), sky, config, config["theme"])
    return "\n".join(
        "".join(cells.get((y, x), (" ",))[0] for x in range(cols)).rstrip()
        for y in range(rows)
    )


def run(stdscr, config, args) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    pairs = make_pairs(stdscr, config)
    speed = max(0.1, float(config["animation"].get("star_speed", 1.0)))
    stdscr.timeout(max(25, int(120 / speed)))
    sky = None
    size = None

    while True:
        rows, cols = stdscr.getmaxyx()
        if size != (rows, cols):
            size = (rows, cols)
            box = layout(rows, cols, bool(config["display"].get("show_seconds", True)), config["display"].get("scale", "auto"), config)[4]
            enabled = bool(config["animation"].get("stars", True)) and not args.no_stars
            sky = Sky(rows, cols, box, config["animation"], enabled=enabled)

        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), 27, 3):
            return
        if sky and not args.no_stars:
            sky.tick()

        stdscr.erase()
        if rows < 10 or cols < 30:
            message = "Window too small"
            stdscr.addstr(0, 0, message[: max(0, cols - 1)])
        else:
            cells = build_cells(rows, cols, time.localtime(), sky, config, config["theme"])
            for (y, x), (char, color, bold) in cells.items():
                if 0 <= y < rows and 0 <= x < cols:
                    try:
                        stdscr.addstr(y, x, char, pairs.get(color, pairs["title"]) | (curses.A_BOLD if bold else 0))
                    except curses.error:
                        pass
        stdscr.refresh()
