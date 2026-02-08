from __future__ import annotations

from typing import Any

from game.state import GameState
from game.story.missions import MISSIONS
from game.enemies import ENEMIES
from game.items import ITEMS, get_item


def mission_objective_text(mission_id: str) -> str:
    mission = MISSIONS.get(mission_id)
    if mission is None:
        return ""
    if not mission.objectives:
        return mission.description
    obj = mission.objectives[0]
    t = str(obj.get("type", ""))
    if t == "collect_item":
        item_id = str(obj.get("item_id", ""))
        count = int(obj.get("count", 1))
        name = get_item(item_id).name if item_id in ITEMS else item_id
        return f"Collect: {name} x{count}"
    if t == "reach_floor":
        dungeon_id = str(obj.get("dungeon_id", ""))
        floor = int(obj.get("floor", 1))
        return f"Reach: {dungeon_id} floor {floor}"
    if t == "defeat_enemy":
        enemy_id = str(obj.get("enemy_id", ""))
        count = int(obj.get("count", 1))
        name = ENEMIES[enemy_id].name if enemy_id in ENEMIES else enemy_id
        return f"Defeat: {name} x{count}"
    if t == "rescue_miners":
        count = int(obj.get("count", 1))
        have = int(getattr(state, "rescued_miners_total", 0))
        return f"Rescue miners: {have}/{count}"
    return mission.description


def is_mission_complete(
    state: GameState,
    mission_id: str,
    *,
    dungeon_id: str | None = None,
    floor: int | None = None,
) -> bool:
    mission = MISSIONS.get(mission_id)
    if mission is None:
        return False
    for obj in mission.objectives:
        if not _objective_complete(state, obj, dungeon_id=dungeon_id, floor=floor):
            return False
    return True


def _objective_complete(
    state: GameState,
    obj: dict[str, Any],
    *,
    dungeon_id: str | None,
    floor: int | None,
) -> bool:
    t = str(obj.get("type", ""))
    if t == "collect_item":
        item_id = str(obj.get("item_id", ""))
        count = int(obj.get("count", 1))
        return state.item_count(item_id) >= count
    if t == "reach_floor":
        needed_dungeon = str(obj.get("dungeon_id", ""))
        needed_floor = int(obj.get("floor", 1))
        if dungeon_id is None or floor is None:
            return False
        return dungeon_id == needed_dungeon and floor >= needed_floor
    if t == "defeat_enemy":
        enemy_id = str(obj.get("enemy_id", ""))
        count = int(obj.get("count", 1))
        base = int((state.mission_kill_baseline or {}).get(enemy_id, 0))
        have = int((state.kill_log or {}).get(enemy_id, 0)) - base
        return have >= count
    if t == "rescue_miners":
        count = int(obj.get("count", 1))
        have = int(getattr(state, "rescued_miners_total", 0))
        return have >= count
    return False
