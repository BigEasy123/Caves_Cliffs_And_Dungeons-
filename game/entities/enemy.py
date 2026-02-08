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
    defense: int = 0
    aggro_range: int = 5
    aggro_turns: int = 0
    move_interval: int = 2
    attack_interval: int = 1
    behavior: str = "melee"
    ranged_range: int = 0
    poison_turns: int = 0
    poison_damage: int = 0
    stunned_turns: int = 0
    patrol_dx: int = 1
    _move_phase: int = 0
    _attack_phase: int = 0

    def is_alive(self) -> bool:
        return self.hp > 0

    def should_move(self, turn: int) -> bool:
        return (turn + self._move_phase) % max(1, self.move_interval) == 0

    def should_attack(self, turn: int) -> bool:
        return (turn + self._attack_phase) % max(1, self.attack_interval) == 0
