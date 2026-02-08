from __future__ import annotations

from dataclasses import dataclass
from random import Random

from game.entities.enemy import Enemy


@dataclass(frozen=True)
class EnemyDef:
    enemy_id: str
    name: str
    base_hp: int
    hp_per_floor: int
    attack: int
    defense: int
    aggro_range: int
    move_interval: int
    attack_interval: int


ENEMIES: dict[str, EnemyDef] = {
    "raider": EnemyDef(
        enemy_id="raider",
        name="Ruins Raider",
        base_hp=7,
        hp_per_floor=2,
        attack=3,
        defense=0,
        aggro_range=5,
        move_interval=2,
        attack_interval=2,
    ),
    "bat": EnemyDef(
        enemy_id="bat",
        name="Cave Bat",
        base_hp=4,
        hp_per_floor=1,
        attack=2,
        defense=0,
        aggro_range=3,
        move_interval=1,
        attack_interval=2,
    ),
    "guardian": EnemyDef(
        enemy_id="guardian",
        name="Stone Guardian",
        base_hp=12,
        hp_per_floor=3,
        attack=4,
        defense=1,
        aggro_range=6,
        move_interval=3,
        attack_interval=2,
    ),
}


def spawn_enemy(enemy_id: str, *, x: int, y: int, floor: int, rng: Random) -> Enemy:
    d = ENEMIES[enemy_id]
    hp = d.base_hp + d.hp_per_floor * max(0, floor - 1)
    return Enemy(
        enemy_id=d.enemy_id,
        name=d.name,
        x=x,
        y=y,
        max_hp=hp,
        hp=hp,
        attack=d.attack + floor // 3,
        defense=d.defense,
        aggro_range=d.aggro_range,
        move_interval=d.move_interval,
        attack_interval=d.attack_interval,
        _move_phase=rng.randint(0, max(0, d.move_interval - 1)),
        _attack_phase=rng.randint(0, max(0, d.attack_interval - 1)),
    )


def enemy_table_for_dungeon(dungeon_id: str, floor: int) -> list[str]:
    if dungeon_id == "jungle_cavern":
        return ["bat", "raider", "guardian"] if floor >= 4 else ["bat", "raider"]
    # temple_ruins default
    return ["raider", "bat"] if floor <= 2 else ["raider", "bat", "guardian"]

