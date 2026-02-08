from __future__ import annotations

from dataclasses import dataclass, field

from game.state import GameState
from typing import Any

from game.data_loader import load_json

@dataclass(frozen=True)
class MissionDef:
    mission_id: str
    name: str
    description: str
    mission_type: str = "misc"  # bounty | rescue | escort | misc
    min_chapter: int = 1
    accept_lines: list[str] = field(default_factory=list)
    turn_in_lines: list[str] = field(default_factory=list)
    reward_gold: int = 0
    reward_guild_xp: int = 0
    reward_items: dict[str, int] = field(default_factory=dict)
    consume_items: dict[str, int] = field(default_factory=dict)
    objectives: list[dict[str, Any]] = field(default_factory=list)


_DEFAULT_MISSIONS: dict[str, MissionDef] = {
    "relic_shard": MissionDef(
        mission_id="relic_shard",
        name="A Shard of Truth",
        description="Find a Relic Shard in the Temple Ruins.",
        mission_type="rescue",
        min_chapter=1,
        accept_lines=[
            "We need proof the ruins have re-opened.",
            "Bring back a Relic Shard from the Temple Ruins and we'll pay you for the risk.",
        ],
        turn_in_lines=[
            "A Relic Shard... the markings are real.",
            "Good work. This will help the Archivist decode the murals.",
        ],
        reward_gold=60,
        reward_guild_xp=45,
        reward_items={"potion_small": 1},
        consume_items={"relic_shard": 1},
        objectives=[{"type": "collect_item", "item_id": "relic_shard", "count": 1}],
    ),
    "reach_floor_3": MissionDef(
        mission_id="reach_floor_3",
        name="Deeper Echoes",
        description="Reach Floor 3 of the Temple Ruins.",
        mission_type="escort",
        min_chapter=1,
        accept_lines=[
            "The surface chambers are picked clean.",
            "Go deeper—reach Floor 3—and report what you find.",
        ],
        turn_in_lines=[
            "So the tremors continue even at Floor 3...",
            "Here. You'll need supplies if you're going back down.",
        ],
        reward_gold=40,
        reward_guild_xp=55,
        reward_items={"torch": 1},
        objectives=[{"type": "reach_floor", "dungeon_id": "temple_ruins", "floor": 3}],
    ),
}


def _missions_from_json(data: dict[str, Any]) -> dict[str, MissionDef]:
    missions: dict[str, MissionDef] = {}
    for mission_id, raw in data.items():
        if not isinstance(raw, dict):
            continue
        missions[mission_id] = MissionDef(
            mission_id=mission_id,
            name=str(raw.get("name", mission_id)),
            description=str(raw.get("description", "")),
            mission_type=str(raw.get("mission_type", "misc")),
            min_chapter=int(raw.get("min_chapter", 1)),
            accept_lines=list(raw.get("accept_lines", []) or []),
            turn_in_lines=list(raw.get("turn_in_lines", []) or []),
            reward_gold=int(raw.get("reward_gold", 0)),
            reward_guild_xp=int(raw.get("reward_guild_xp", 0)),
            reward_items=dict(raw.get("reward_items", {}) or {}),
            consume_items=dict(raw.get("consume_items", {}) or {}),
            objectives=list(raw.get("objectives", []) or []),
        )
    return missions


MISSIONS: dict[str, MissionDef] = _DEFAULT_MISSIONS
_loaded = load_json("data/missions.json")
if isinstance(_loaded, dict):
    parsed = _missions_from_json(_loaded)
    if parsed:
        MISSIONS = parsed


def is_turn_in_available(state: GameState, mission_id: str) -> bool:
    return mission_id in state.completed_missions and mission_id not in state.claimed_missions


def apply_turn_in_rewards(state: GameState, mission_id: str) -> bool:
    mission = MISSIONS[mission_id]
    for item_id, count in mission.consume_items.items():
        if state.item_count(item_id) < count:
            return False
    for item_id, count in mission.consume_items.items():
        state.remove_item(item_id, count)
    state.gold += mission.reward_gold
    state.add_guild_xp(mission.reward_guild_xp)
    for item_id, count in mission.reward_items.items():
        state.add_item(item_id, count)
    state.claimed_missions.add(mission_id)
    return True
