from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from game.state import GameState
from game.story.flags import FLAG_GOT_TEMPLE_PASS, FLAG_MET_GUARD, FLAG_MET_MAYOR, FLAG_MET_PROFESSOR, FLAG_MET_SCOUT


@dataclass(frozen=True)
class DialogueScript:
    speaker: str
    lines: list[str]
    on_finish: Callable[[GameState], None] | None = None


def format_dialogue_line(text: str, state: GameState) -> str:
    try:
        player = (state.player_name or "").strip() or "Adventurer"
    except Exception:
        player = "Adventurer"
    mapping = {
        "player": player,
        "chapter": int(getattr(state, "chapter", 1)),
        "guild_rank": int(getattr(state, "guild_rank", 1)),
        "combat_level": int(getattr(state, "combat_level", 1)),
    }
    try:
        return text.format(**mapping)
    except Exception:
        return text


def format_dialogue_script(script: DialogueScript, state: GameState) -> DialogueScript:
    return DialogueScript(
        speaker=script.speaker,
        lines=[format_dialogue_line(l, state) for l in script.lines],
        on_finish=script.on_finish,
    )


def script_for_npc(npc_id: str, state: GameState) -> DialogueScript | None:
    chapter = int(getattr(state, "chapter", 1))
    if npc_id == "professor":
        if not state.has(FLAG_MET_PROFESSOR):
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "{player}. I read your essay twice.",
                    "I know you feel stuck—tired, behind, invisible. But your mind isn't dull. It's starving.",
                    "I can keep you enrolled… if you study abroad with us.",
                    "We call it the Guild. Officially, we fund expeditions. Unofficially… we protect history itself.",
                    "There's a cult trying to corrupt the timeline—turning humanity back toward the stone ages, one fracture at a time.",
                    "If you join, you won't just learn history. You'll defend it.",
                ],
                on_finish=lambda s: s.set(FLAG_MET_PROFESSOR),
            )
        if chapter <= 2:
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "Start small. Prove you can come back alive.",
                    "The Guild will trust you when you bring results, not bravado.",
                ],
            )
        if chapter <= 5:
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "The deeper you go, the less these ruins feel like accidents.",
                    "If you hear whispers about 'purifying the past'—write them down. Names matter.",
                ],
            )
        return DialogueScript(
            speaker="Professor",
            lines=[
                "History doesn't end. It transforms.",
                "And so do you, {player}.",
            ],
        )
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
        if chapter >= 4:
            return DialogueScript(
                speaker="Mayor",
                lines=[
                    "People say the nights feel… wrong lately.",
                    "If you're chasing answers, start with the Guild. They see more than we do.",
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
        if chapter >= 3:
            return DialogueScript(
                speaker="Archivist",
                lines=[
                    "Some texts don't just describe history. They argue with it.",
                    "If you find symbols that repeat, sketch them. Patterns are where the truth hides.",
                ],
            )
        return DialogueScript(
            speaker="Archivist",
            lines=[
                "History lives in layers. Don't rush the first step.",
                "The Mayor usually knows when it's safe to venture out.",
            ],
        )

    if npc_id == "guard":
        if not state.has(FLAG_MET_GUARD):
            return DialogueScript(
                speaker="Guard",
                lines=[
                    "Checkpoint's open for Guild business only.",
                    "Show the pass and keep moving. The outskirts aren't safe after dark.",
                ],
                on_finish=lambda s: s.set(FLAG_MET_GUARD),
            )
        if chapter >= 4:
            return DialogueScript(
                speaker="Guard",
                lines=[
                    "You hear about that cult? Folks call them 'the Regressors'.",
                    "If you see torches that burn cold… run.",
                ],
            )
        return DialogueScript(speaker="Guard", lines=["Stay sharp out there."])

    if npc_id == "scout":
        if not state.has(FLAG_MET_SCOUT):
            return DialogueScript(
                speaker="Scout",
                lines=[
                    "You heading out? Good. Someone needs to map those new trails.",
                    "If you reach the caverns, mark your turns. The jungle makes fools of confident people.",
                ],
                on_finish=lambda s: s.set(FLAG_MET_SCOUT),
            )
        if chapter >= 2:
            return DialogueScript(
                speaker="Scout",
                lines=[
                    "The jungle paths shift. Like someone keeps rewriting the map.",
                    "If the Guild asks, tell them: it's not weather. It's intent.",
                ],
            )
        return DialogueScript(speaker="Scout", lines=["Bring back notes. Not trophies."])

    return None
