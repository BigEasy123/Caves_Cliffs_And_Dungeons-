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
    "cave_in_rescue": MissionDef(
        mission_id="cave_in_rescue",
        name="Cave-in: Rescue Operation",
        description="A remote mine has collapsed. Rescue trapped miners and escort them home.",
        mission_type="rescue",
        min_chapter=3,
        accept_lines=[
            "We got a distress call from miners in a remote shaft.",
            "The Children of the Nephil are there too—playing hero. Don't trust them.",
            "Rescue 26 miners and escort them out. Then find the head miner in the deepest shaft.",
        ],
        turn_in_lines=[
            "They're alive... you actually pulled it off.",
            "The public loves a good rescue story. Be careful who gets to tell it.",
        ],
        reward_gold=160,
        reward_guild_xp=170,
        reward_items={"potion_medium": 1},
        consume_items={"head_miner_token": 1},
        objectives=[{"type": "rescue_miners", "count": 26}, {"type": "collect_item", "item_id": "head_miner_token", "count": 1}],
    ),
    "rival_hostage": MissionDef(
        mission_id="rival_hostage",
        name="Rivalry: Hostage Rescue",
        description="Your rival went missing on a bragging spree. Rescue them from the Children of the Nephil.",
        mission_type="rescue",
        min_chapter=4,
        accept_lines=[
            "Your rival hasn't checked in. Not like them.",
            "A rumor says the Children of the Nephil took someone into a hideout.",
            "Bring them back. Alive.",
        ],
        turn_in_lines=[
            "They're alive... barely.",
            "The rivalry can wait. This was a warning.",
        ],
        reward_gold=140,
        reward_guild_xp=150,
        reward_items={"potion_medium": 1},
        consume_items={"rival_rescue_badge": 1},
        objectives=[{"type": "collect_item", "item_id": "rival_rescue_badge", "count": 1}],
    ),
    "babel_tablet": MissionDef(
        mission_id="babel_tablet",
        name="Not What They Seem (I): Babel Tablet",
        description="Investigate the strange tower and recover evidence of mixed languages.",
        mission_type="rescue",
        min_chapter=5,
        accept_lines=[
            "A new civilization has appeared around a giant tower.",
            "The writings are an impossible mix of languages—like they were fused together.",
            "Bring back a Babel Tablet so the Archivist can study it.",
        ],
        turn_in_lines=[
            "These scripts... they're stacked like layers in time.",
            "This tower isn't just old. It's wrong. Keep going.",
        ],
        reward_gold=120,
        reward_guild_xp=130,
        reward_items={"torch": 1},
        consume_items={"babel_tablet": 1},
        objectives=[{"type": "collect_item", "item_id": "babel_tablet", "count": 1}],
    ),
    "nimrods_bow_find": MissionDef(
        mission_id="nimrods_bow_find",
        name="Not What They Seem (I): Nimrod's Bow",
        description="Reach the bottom of the tower and recover Nimrod's Bow.",
        mission_type="escort",
        min_chapter=5,
        accept_lines=[
            "Reports say the tower has a deep foundation—stairs that shouldn't exist.",
            "At the bottom is an artifact: Nimrod's Bow.",
            "Bring it back. Keep it close. Don't trust the new recruit.",
        ],
        turn_in_lines=[
            "You actually found it...",
            "Hold on—someone's missing. Where is the recruit?",
        ],
        reward_gold=180,
        reward_guild_xp=190,
        reward_items={"potion_medium": 1},
        consume_items={"nimrods_bow": 1},
        objectives=[{"type": "collect_item", "item_id": "nimrods_bow", "count": 1}],
    ),
    "nimrods_bow_retrieve": MissionDef(
        mission_id="nimrods_bow_retrieve",
        name="Not What They Seem (II): Steal It Back",
        description="The Children stole the bow. Infiltrate their vault and retrieve it.",
        mission_type="rescue",
        min_chapter=6,
        accept_lines=[
            "The recruit was an imposter.",
            "The bow is in a Children vault. If they use it, the timeline fractures.",
            "Go. Retrieve Nimrod's Bow.",
        ],
        turn_in_lines=[
            "You got it back.",
            "Now we do the hard part: we destroy it.",
        ],
        reward_gold=160,
        reward_guild_xp=170,
        reward_items={"antidote": 1},
        consume_items={"nimrods_bow": 1},
        objectives=[{"type": "collect_item", "item_id": "nimrods_bow", "count": 1}],
    ),
    "nimrods_bow_destroy": MissionDef(
        mission_id="nimrods_bow_destroy",
        name="Not What They Seem (II): Destroy the Bow",
        description="Hand over Nimrod's Bow so the Guild can destroy it safely.",
        mission_type="escort",
        min_chapter=6,
        accept_lines=[
            "We can't keep it. Not even locked away.",
            "Bring the bow to the Professor. We'll destroy it before the Children can trace it.",
        ],
        turn_in_lines=[
            "It's done. The bow is gone.",
            "But the Children now know exactly who you are.",
        ],
        reward_gold=220,
        reward_guild_xp=230,
        reward_items={"iron_ring": 1},
        consume_items={"nimrods_bow": 1},
        objectives=[{"type": "collect_item", "item_id": "nimrods_bow", "count": 1}],
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
    state.missions_turned_in_total = int(getattr(state, "missions_turned_in_total", 0)) + 1
    # Track relic turn-ins for rivalry (covers Nephil relics + any future relics).
    for item_id, count in mission.consume_items.items():
        if "relic" in str(item_id):
            state.relics_turned_in_total = int(getattr(state, "relics_turned_in_total", 0)) + int(count)
    for item_id, count in mission.reward_items.items():
        state.add_item(item_id, count)
    state.claimed_missions.add(mission_id)

    # Rival progression (simple deterministic "they also did stuff" model).
    try:
        import zlib

        h = zlib.crc32(mission_id.encode("utf-8"))
        if h % 3 != 0:
            state.rival_missions = int(getattr(state, "rival_missions", 0)) + 1
        if h % 5 == 0 and any("relic" in str(i) for i in mission.consume_items.keys()):
            state.rival_relics = int(getattr(state, "rival_relics", 0)) + 1
        if h % 7 == 0:
            state.rival_rescues = int(getattr(state, "rival_rescues", 0)) + 1
    except Exception:
        pass
    return True
