from __future__ import annotations

from enum import StrEnum


class Direction(StrEnum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


def direction_from_step(dx: int, dy: int, *, default: Direction = Direction.DOWN) -> Direction:
    if dx > 0:
        return Direction.RIGHT
    if dx < 0:
        return Direction.LEFT
    if dy > 0:
        return Direction.DOWN
    if dy < 0:
        return Direction.UP
    return default

