from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Star:
    y: int
    x: int
    age: float
    life: int
    speed: float

    def look(self) -> tuple[str, str]:
        stages = [(".", "dim"), ("+", "mid"), ("*", "bright"), ("+", "mid"), (".", "dim")]
        index = min(len(stages) - 1, int(self.age / self.life * len(stages)))
        return stages[index]


class Sky:
    def __init__(self, rows: int, cols: int, box: tuple[int, int, int, int], settings: dict, enabled: bool = True):
        self.rng = random.Random()
        self.rows, self.cols, self.box = rows, cols, box
        self.settings = settings
        self.stars: list[Star] = []
        if enabled:
            density = max(0.05, float(settings.get("star_density", 1.0)))
            count = max(5, int(rows * cols / 70 * density))
            self.stars = [self._new(self.rng.randint(0, 30)) for _ in range(count)]
            self.stars = [star for star in self.stars if star]

    def _new(self, age: float = 0) -> Star | None:
        y0, y1, x0, x1 = self.box
        life_min = max(2, int(self.settings.get("star_life_min", 14)))
        life_max = max(life_min, int(self.settings.get("star_life_max", 45)))
        speed = max(0.05, float(self.settings.get("star_speed", 1.0)))
        for _ in range(40):
            y, x = self.rng.randrange(self.rows), self.rng.randrange(self.cols)
            if not (y0 <= y <= y1 and x0 <= x <= x1):
                return Star(y, x, age, self.rng.randint(life_min, life_max), speed)
        return None

    def tick(self) -> None:
        for index, star in enumerate(self.stars):
            star.age += star.speed
            if star.age >= star.life:
                fresh = self._new()
                if fresh:
                    self.stars[index] = fresh
                else:
                    star.age = 0


def animation_state(kind: str, now: float, interval: float, duration: float) -> tuple[bool, str, int]:
    """Return visible, strength, and horizontal offset for a decoration."""
    kind = (kind or "none").lower()
    interval = max(0.1, float(interval))
    duration = max(0.1, min(float(duration), interval))

    if kind in ("none", "static"):
        return True, "bright", 0

    if kind == "blink":
        return (int(now * 2) % 2 == 0), "bright", 0

    if kind == "pulse":
        phase = int(now * 2) % 4
        return True, ("bright" if phase in (1, 2) else "mid"), 0

    elapsed = now % interval
    if elapsed >= duration:
        return False, "dim", 0

    progress = elapsed / duration
    if kind == "slide":
        offset = max(0, int((1.0 - progress) * 8))
        strength = "bright" if progress > 0.35 else "mid"
        return True, strength, offset

    # fade: appear -> bright -> dim, then disappear until the next interval.
    if progress < 0.25 or progress > 0.80:
        return True, "dim", 0
    return True, "bright", 0
