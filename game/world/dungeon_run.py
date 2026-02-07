from __future__ import annotations

from dataclasses import dataclass, field
import zlib


@dataclass
class DungeonRun:
    dungeon_id: str
    dungeon_name: str
    max_floor: int = 5
    floor: int = 1
    seed_base: int = 0
    _floor_seeds: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.seed_base == 0:
            # Stable seed derived from dungeon_id (avoid Python's randomized hash()).
            self.seed_base = zlib.crc32(self.dungeon_id.encode("utf-8")) % 2_000_000_000

    def seed_for_floor(self, floor: int) -> int:
        if floor not in self._floor_seeds:
            self._floor_seeds[floor] = self.seed_base + floor * 1013
        return self._floor_seeds[floor]
