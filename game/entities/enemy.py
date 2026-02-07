from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Enemy:
    enemy_id: str
    name: str
    x: int
    y: int
    max_hp: int
    hp: int
    attack: int

    def is_alive(self) -> bool:
        return self.hp > 0

