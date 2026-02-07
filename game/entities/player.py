from __future__ import annotations

from dataclasses import dataclass
from random import choice


Grid = list[list[int]]


@dataclass
class GridPlayer:
    x: int
    y: int

    @staticmethod
    def spawn_on_floor(grid: Grid) -> "GridPlayer":
        floors: list[tuple[int, int]] = []
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == 0:
                    floors.append((x, y))
        if not floors:
            return GridPlayer(1, 1)
        x, y = choice(floors)
        return GridPlayer(x, y)

    def try_move(self, dx: int, dy: int, grid: Grid, *, walls: set[int] | None = None) -> None:
        nx = self.x + dx
        ny = self.y + dy
        if ny < 0 or ny >= len(grid):
            return
        if nx < 0 or nx >= len(grid[0]):
            return
        if walls is None:
            walls = {1}
        if grid[ny][nx] in walls:
            return
        self.x = nx
        self.y = ny
