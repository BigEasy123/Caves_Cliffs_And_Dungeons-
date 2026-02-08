from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from game.entities.enemy import Enemy
from game.data_loader import load_json


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
    behavior: str = "melee"
    ranged_range: int = 0
    poison_turns: int = 0
    poison_damage: int = 0


_DEFAULT_ENEMIES: dict[str, EnemyDef] = {
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
        behavior="melee",
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
        behavior="melee",
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
        behavior="melee_patrol",
    ),
    "archer": EnemyDef(
        enemy_id="archer",
        name="Rogue Archer",
        base_hp=6,
        hp_per_floor=2,
        attack=3,
        defense=0,
        aggro_range=7,
        move_interval=2,
        attack_interval=2,
        behavior="ranged",
        ranged_range=4,
    ),
    "snake": EnemyDef(
        enemy_id="snake",
        name="Jungle Snake",
        base_hp=5,
        hp_per_floor=2,
        attack=2,
        defense=0,
        aggro_range=5,
        move_interval=2,
        attack_interval=2,
        behavior="poison_melee",
        poison_turns=3,
        poison_damage=1,
    ),
}


def _enemies_from_json(data: dict[str, Any]) -> dict[str, EnemyDef]:
    enemies: dict[str, EnemyDef] = {}
    for enemy_id, raw in data.items():
        if not isinstance(raw, dict):
            continue
        enemies[enemy_id] = EnemyDef(
            enemy_id=enemy_id,
            name=str(raw.get("name", enemy_id)),
            base_hp=int(raw.get("base_hp", 1)),
            hp_per_floor=int(raw.get("hp_per_floor", 0)),
            attack=int(raw.get("attack", 1)),
            defense=int(raw.get("defense", 0)),
            aggro_range=int(raw.get("aggro_range", 5)),
            move_interval=int(raw.get("move_interval", 2)),
            attack_interval=int(raw.get("attack_interval", 2)),
            behavior=str(raw.get("behavior", "melee")),
            ranged_range=int(raw.get("ranged_range", 0)),
            poison_turns=int(raw.get("poison_turns", 0)),
            poison_damage=int(raw.get("poison_damage", 0)),
        )
    return enemies


ENEMIES: dict[str, EnemyDef] = _DEFAULT_ENEMIES
_loaded = load_json("data/enemies.json")
if isinstance(_loaded, dict):
    parsed = _enemies_from_json(_loaded)
    if parsed:
        ENEMIES = parsed


def spawn_enemy(enemy_id: str, *, x: int, y: int, floor: int, combat_level: int = 1, rng: Random) -> Enemy:
    d = ENEMIES[enemy_id]
    difficulty = max(0, int(combat_level) - 1)
    effective_floor = floor + (difficulty // 2)
    hp = d.base_hp + d.hp_per_floor * max(0, effective_floor - 1)
    return Enemy(
        enemy_id=d.enemy_id,
        name=d.name,
        x=x,
        y=y,
        max_hp=hp,
        hp=hp,
        attack=d.attack + effective_floor // 3 + (difficulty // 4),
        defense=d.defense + (difficulty // 5),
        aggro_range=d.aggro_range,
        move_interval=d.move_interval,
        attack_interval=d.attack_interval,
        behavior=d.behavior,
        ranged_range=d.ranged_range,
        poison_turns=d.poison_turns,
        poison_damage=d.poison_damage,
        patrol_dx=rng.choice([-1, 1]),
        _move_phase=rng.randint(0, max(0, d.move_interval - 1)),
        _attack_phase=rng.randint(0, max(0, d.attack_interval - 1)),
    )


def enemy_table_for_dungeon(dungeon_id: str, floor: int) -> list[str]:
    if dungeon_id == "nephil_dunes":
        if floor <= 2:
            return ["giant_scout", "giant_warrior"]
        if floor <= 4:
            return ["giant_scout", "giant_warrior", "giant_shaman"]
        return ["giant_warrior", "giant_shaman", "giant_brute"]
    if dungeon_id == "nephil_oasis":
        if floor <= 2:
            return ["giant_scout", "giant_shaman"]
        if floor <= 4:
            return ["giant_warrior", "giant_shaman", "giant_brute"]
        return ["giant_warrior", "giant_shaman", "giant_brute"]
    if dungeon_id == "nephil_tomb":
        if floor <= 2:
            return ["giant_warrior", "giant_shaman"]
        if floor <= 4:
            return ["giant_warrior", "giant_shaman", "giant_brute"]
        return ["giant_warrior", "giant_shaman", "giant_brute"]
    if dungeon_id == "collapsed_mines":
        if floor <= 2:
            return ["bat", "cult_saboteur"]
        if floor <= 4:
            return ["cult_saboteur", "cult_initiate", "raider"]
        return ["cult_saboteur", "cult_initiate", "guardian"]
    if dungeon_id == "deep_shaft":
        if floor <= 2:
            return ["cult_saboteur", "cult_initiate"]
        if floor <= 4:
            return ["cult_saboteur", "cult_initiate", "guardian"]
        return ["cult_saboteur", "cult_initiate", "giant_scout"]
    if dungeon_id == "children_hideout":
        if floor <= 2:
            return ["cult_saboteur", "cult_initiate"]
        if floor <= 4:
            return ["cult_saboteur", "cult_initiate", "raider"]
        return ["cult_saboteur", "cult_initiate", "giant_scout"]
    if dungeon_id == "babel_tower":
        if floor <= 2:
            return ["raider", "babel_scribe"]
        if floor <= 4:
            return ["babel_scribe", "babel_sentinel", "archer"]
        return ["babel_scribe", "babel_sentinel", "guardian"]
    if dungeon_id == "children_vault":
        if floor <= 2:
            return ["cult_saboteur", "cult_initiate"]
        if floor <= 4:
            return ["cult_saboteur", "cult_initiate", "children_enforcer"]
        return ["cult_initiate", "children_enforcer", "giant_scout"]
    if dungeon_id == "jungle_cavern":
        if floor <= 2:
            return ["snake", "bat"]
        if floor <= 4:
            return ["snake", "bat", "raider"]
        return ["snake", "bat", "raider", "archer", "guardian"]
    # temple_ruins default
    if floor <= 2:
        return ["raider", "bat"]
    if floor <= 4:
        return ["raider", "bat", "archer"]
    return ["raider", "bat", "archer", "guardian"]
