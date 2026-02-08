from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from game.state import GameState
from game.story.flags import FLAG_GOT_TEMPLE_PASS, FLAG_MET_MAYOR


@dataclass(frozen=True)
class DialogueScript:
    speaker: str
    lines: list[str]
    on_finish: Callable[[GameState], None] | None = None


def script_for_npc(npc_id: str, state: GameState) -> DialogueScript | None:
    if npc_id == "mayor":
        if not state.has(FLAG_MET_MAYOR):
            return DialogueScript(
                speaker="Mayor",
                lines=[
                    "Ah—you're the new face in town.",
                    "Strange tremors opened the old Temple Ruins again.",
                    "If you're set on exploring, take this pass. It will get you through the checkpoint.",
                ],
                on_finish=lambda s: (s.set(FLAG_MET_MAYOR), s.set(FLAG_GOT_TEMPLE_PASS)),
            )
        if "reach_floor_3" in state.completed_missions and "reach_floor_3" not in state.claimed_missions:
            return DialogueScript(
                speaker="Mayor",
                lines=[
                    "Floor 3? Then the stories are true...",
                    "Check in at the Guild. They'll want a report—and you deserve your pay.",
                ],
            )
        return DialogueScript(
            speaker="Mayor",
            lines=[
                "Be careful in the ruins.",
                "If you find any relics with markings, bring sketches back to town.",
            ],
        )

    if npc_id == "archivist":
        if state.has(FLAG_GOT_TEMPLE_PASS):
            return DialogueScript(
                speaker="Archivist",
                lines=[
                    "Temple Ruins, hm? The murals mention a 'Sun Dial Key'.",
                    "Watch for a chamber with four pillars—each points to a cardinal wind.",
                ],
            )
        if "relic_shard" in state.completed_missions and "relic_shard" not in state.claimed_missions:
            return DialogueScript(
                speaker="Archivist",
                lines=[
                    "You found a shard? Don't lose it.",
                    "The Guild can catalog it properly—and pay you for it.",
                ],
            )
        return DialogueScript(
            speaker="Archivist",
            lines=[
                "History lives in layers. Don't rush the first step.",
                "The Mayor usually knows when it's safe to venture out.",
            ],
        )

    return None
