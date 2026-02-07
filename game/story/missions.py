from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MissionDef:
    mission_id: str
    name: str
    description: str


MISSIONS: dict[str, MissionDef] = {
    "relic_shard": MissionDef(
        mission_id="relic_shard",
        name="A Shard of Truth",
        description="Find a Relic Shard in the Temple Ruins.",
    ),
    "reach_floor_3": MissionDef(
        mission_id="reach_floor_3",
        name="Deeper Echoes",
        description="Reach Floor 3 of the Temple Ruins.",
    ),
}

