from __future__ import annotations

from dataclasses import dataclass, field

from game.state import GameState


@dataclass(frozen=True)
class MissionDef:
    mission_id: str
    name: str
    description: str
    accept_lines: list[str] = field(default_factory=list)
    turn_in_lines: list[str] = field(default_factory=list)
    reward_gold: int = 0
    reward_items: dict[str, int] = field(default_factory=dict)
    consume_items: dict[str, int] = field(default_factory=dict)


MISSIONS: dict[str, MissionDef] = {
    "relic_shard": MissionDef(
        mission_id="relic_shard",
        name="A Shard of Truth",
        description="Find a Relic Shard in the Temple Ruins.",
        accept_lines=[
            "We need proof the ruins have re-opened.",
            "Bring back a Relic Shard from the Temple Ruins and we'll pay you for the risk.",
        ],
        turn_in_lines=[
            "A Relic Shard... the markings are real.",
            "Good work. This will help the Archivist decode the murals.",
        ],
        reward_gold=60,
        reward_items={"potion_small": 1},
        consume_items={"relic_shard": 1},
    ),
    "reach_floor_3": MissionDef(
        mission_id="reach_floor_3",
        name="Deeper Echoes",
        description="Reach Floor 3 of the Temple Ruins.",
        accept_lines=[
            "The surface chambers are picked clean.",
            "Go deeper—reach Floor 3—and report what you find.",
        ],
        turn_in_lines=[
            "So the tremors continue even at Floor 3...",
            "Here. You'll need supplies if you're going back down.",
        ],
        reward_gold=40,
        reward_items={"torch": 1},
    ),
}


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
    for item_id, count in mission.reward_items.items():
        state.add_item(item_id, count)
    state.claimed_missions.add(mission_id)
    return True
