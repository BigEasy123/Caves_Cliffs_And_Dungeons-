from __future__ import annotations

import random


def _carve_room(grid: list[list[int]], x: int, y: int, w: int, h: int) -> None:
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            grid[yy][xx] = 0


def _carve_h_corridor(grid: list[list[int]], x1: int, x2: int, y: int) -> None:
    if x2 < x1:
        x1, x2 = x2, x1
    for x in range(x1, x2 + 1):
        grid[y][x] = 0


def _carve_v_corridor(grid: list[list[int]], y1: int, y2: int, x: int) -> None:
    if y2 < y1:
        y1, y2 = y2, y1
    for y in range(y1, y2 + 1):
        grid[y][x] = 0


def generate_dungeon(
    width: int,
    height: int,
    *,
    seed: int | None = None,
    place_stairs_up: bool = True,
    place_stairs_down: bool = True,
) -> list[list[int]]:
    """
    Returns a 2D grid: 0=floor, 1=wall, 2=stairs_down, 3=stairs_up.
    This is intentionally simple scaffolding that we can iterate on later.
    """
    rng = random.Random(seed)

    grid = [[1 for _ in range(width)] for _ in range(height)]

    rooms: list[tuple[int, int, int, int]] = []
    room_attempts = 60
    for _ in range(room_attempts):
        w = rng.randint(4, 8)
        h = rng.randint(4, 7)
        x = rng.randint(1, max(1, width - w - 2))
        y = rng.randint(1, max(1, height - h - 2))

        rect = (x, y, w, h)
        if _intersects_any(rect, rooms, pad=1):
            continue

        _carve_room(grid, x, y, w, h)
        rooms.append(rect)

        if len(rooms) > 1:
            px, py = _center(rooms[-2])
            cx, cy = _center(rect)
            if rng.random() < 0.5:
                _carve_h_corridor(grid, px, cx, py)
                _carve_v_corridor(grid, py, cy, cx)
            else:
                _carve_v_corridor(grid, py, cy, px)
                _carve_h_corridor(grid, px, cx, cy)

    if not rooms:
        # Fallback: carve a simple central area
        _carve_room(grid, 2, 2, max(3, width - 4), max(3, height - 4))

    _place_stairs(grid, rng, up=place_stairs_up, down=place_stairs_down)
    return grid


def _center(room: tuple[int, int, int, int]) -> tuple[int, int]:
    x, y, w, h = room
    return x + w // 2, y + h // 2


def _intersects_any(
    room: tuple[int, int, int, int],
    rooms: list[tuple[int, int, int, int]],
    *,
    pad: int = 0,
) -> bool:
    x, y, w, h = room
    ax1 = x - pad
    ay1 = y - pad
    ax2 = x + w + pad
    ay2 = y + h + pad

    for rx, ry, rw, rh in rooms:
        bx1 = rx
        by1 = ry
        bx2 = rx + rw
        by2 = ry + rh
        if ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1:
            return True
    return False


def _place_stairs(
    grid: list[list[int]],
    rng: random.Random,
    *,
    up: bool,
    down: bool,
) -> None:
    floors: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == 0:
                floors.append((x, y))

    if not floors:
        return

    rng.shuffle(floors)
    idx = 0
    if up:
        x, y = floors[idx]
        grid[y][x] = 3
        idx += 1
    if down and idx < len(floors):
        x, y = floors[idx]
        grid[y][x] = 2
