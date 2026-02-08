from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from game.state import GameState
from game.story.flags import (
    FLAG_ARROW_TIP_LOST,
    FLAG_CHILDREN_EXPERIMENT_SUCCEEDED,
    FLAG_FOUND_ARROWHEAD_MAP,
    FLAG_CULT_STOLE_CREDIT,
    FLAG_BOW_DESTROYED,
    FLAG_BOW_STOLEN,
    FLAG_GOT_TEMPLE_PASS,
    FLAG_MET_GUARD,
    FLAG_MET_MAYOR,
    FLAG_MET_PROFESSOR,
    FLAG_MET_RECRUIT,
    FLAG_MET_SCOUT,
    FLAG_MET_TA1,
    FLAG_MET_TA2,
    FLAG_RIVAL_KIDNAPPED,
    FLAG_RIVAL_RESCUED,
)
from game.story.factions import CHILDREN_OF_THE_NEPHIL


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
                    f"There's a society trying to corrupt the timeline—{CHILDREN_OF_THE_NEPHIL}.",
                    "They want to send humanity back toward the stone ages, one fracture at a time.",
                    "If you join, you won't just learn history. You'll defend it.",
                ],
                on_finish=lambda s: s.set(FLAG_MET_PROFESSOR),
            )
        if chapter == 2:
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "You're in, officially. That means you get the truth—and the burden.",
                    "The desert reports are real. A lost civilization: the Nephil.",
                    f"Three relics. One {CHILDREN_OF_THE_NEPHIL}. And giants waking up in the sand.",
                    f"Take contracts from the clerk. Bring back relics before {CHILDREN_OF_THE_NEPHIL} can rewrite them.",
                ],
            )
        if chapter == 3:
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "New distress call. A remote mine collapsed—dozens trapped.",
                    f"{CHILDREN_OF_THE_NEPHIL} rushed in first, wearing kindness like a costume.",
                    "Rescue as many as you can. Bring them home. And watch your back.",
                ],
            )
        if chapter == 4:
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "Rivalries can sharpen you… or split you in half.",
                    f"If {CHILDREN_OF_THE_NEPHIL} grabs a weakness, they'll use it.",
                    "If your 'friend' goes missing, you bring them back. Understood?",
                ],
            )
        if chapter == 6:
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "The tower wasn't a myth. It was a trap with a history.",
                    f"If {CHILDREN_OF_THE_NEPHIL} has the bow, we take it back.",
                    "And then we destroy it. No trophies. No excuses.",
                ],
            )
        if chapter == 7:
            if state.has(FLAG_ARROW_TIP_LOST):
                return DialogueScript(
                    speaker="Professor",
                    lines=[
                        "The bow is shattered. But one fragment slipped away.",
                        "We chase it into the ice. Not for gloryâ€”for containment.",
                        "Check the Base Camp board. We'll operate from there until we have a lead.",
                    ],
                )
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "Keep your eyes open out there.",
                    "The world doesn't like it when we break old weapons.",
                ],
            )
        if chapter == 8:
            if state.has(FLAG_FOUND_ARROWHEAD_MAP):
                return DialogueScript(
                    speaker="Professor",
                    lines=[
                        "Across the world... of course.",
                        "If the Children reach that island first, the arrow tip becomes a weapon again.",
                        "Move fast, {player}.",
                    ],
                )
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "We're running out of time.",
                    "Find the map. Then we move.",
                ],
            )
        if chapter == 9:
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "They've gone underground. Deeper than any ruin we've mapped.",
                    "If the stories are true... something like the old flood waits below.",
                    "Don't let them wake it.",
                ],
            )
        if chapter >= 10:
            if state.has(FLAG_CHILDREN_EXPERIMENT_SUCCEEDED):
                return DialogueScript(
                    speaker="Professor",
                    lines=[
                        "Retirement isn't a door. It's a question.",
                        "If you stay, you shape the Guild. If you leave, you carry the truth out into the world.",
                        "Either choice is brave.",
                        "",
                        "But know this: one Children experiment worked.",
                        "We don't know what it made. We only know it moved.",
                    ],
                )
            return DialogueScript(
                speaker="Professor",
                lines=[
                    "The world kept turning.",
                    "So will you, {player}.",
                ],
            )
        if chapter <= 3:
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
        if state.has(FLAG_MET_MAYOR) and chapter >= 7:
            return DialogueScript(
                speaker="Mayor",
                lines=[
                    "The Guild's packing for an expedition. Ice this time.",
                    "If you're going, bring the town back a future.",
                ],
            )
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
        if state.has(FLAG_CULT_STOLE_CREDIT):
            return DialogueScript(
                speaker="Mayor",
                lines=[
                    f"They say {CHILDREN_OF_THE_NEPHIL} saved the miners. That's what the papers say.",
                    "But you look like someone who carried people through darkness.",
                    "If you need allies, the Guild will listen—eventually.",
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
        if chapter >= 10 and state.has(FLAG_CHILDREN_EXPERIMENT_SUCCEEDED):
            return DialogueScript(
                speaker="Archivist",
                lines=[
                    "When villains fail, they usually fail loudly.",
                    "The quiet successes are the ones that haunt the margins of history.",
                ],
            )
        if chapter >= 7:
            return DialogueScript(
                speaker="Archivist",
                lines=[
                    "Ice preserves lies for a long time.",
                    "If you find a map with unfamiliar coastlines... do not assume it's wrong.",
                ],
            )
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
        if chapter == 2:
            return DialogueScript(
                speaker="Archivist",
                lines=[
                    "Nephil? I've only seen the name in contested fragments.",
                    "Three relics is never just archaeology. It's ritual.",
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
                    f"Folks whisper about {CHILDREN_OF_THE_NEPHIL}.",
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

    if npc_id == "recruit":
        if int(getattr(state, "chapter", 1)) < 5:
            return None
        if state.has(FLAG_BOW_DESTROYED):
            return None
        if state.has(FLAG_BOW_STOLEN):
            return DialogueScript(
                speaker="New Recruit",
                lines=[
                    "(The recruit is gone. Only dust remains where they stood.)",
                ],
            )
        if not state.has(FLAG_MET_RECRUIT):
            return DialogueScript(
                speaker="New Recruit",
                lines=[
                    "Hey. I'm new too—guess we're both trying to prove ourselves.",
                    "If you find anything important in that tower, bring it straight here. No detours.",
                ],
                on_finish=lambda s: s.set(FLAG_MET_RECRUIT),
            )
        return DialogueScript(
            speaker="New Recruit",
            lines=[
                "That tower gives me a headache.",
                "Still… artifacts are artifacts. Bring them back fast.",
            ],
        )

    if npc_id == "ta_ren":
        if not state.has(FLAG_MET_TA1):
            return DialogueScript(
                speaker="Ren (TA)",
                lines=[
                    "Hey! You're Professor's new recruit, right?",
                    "I'm Ren—his TA. If you need notes or a friendly face, find me.",
                ],
                on_finish=lambda s: s.set(FLAG_MET_TA1),
            )
        if chapter == 2:
            return DialogueScript(
                speaker="Ren (TA)",
                lines=[
                    "So you're official now. About time.",
                    "If you bring back anything Nephil, label it. The Professor pretends he doesn't care—he does.",
                ],
            )
        if chapter >= 7:
            return DialogueScript(
                speaker="Ren (TA)",
                lines=[
                    "Base camp life is all logistics.",
                    "If you come back with frost on your lashes, drink water anyway. Trust me.",
                ],
            )
        return DialogueScript(speaker="Ren (TA)", lines=["Stay alive, {player}. That's my whole request."])

    if npc_id == "ta_lena":
        if not state.has(FLAG_MET_TA2):
            return DialogueScript(
                speaker="Lena (TA)",
                lines=[
                    "I heard you were joining the Guild.",
                    "I'm Lena. Professor trusts you, so… I will too.",
                ],
                on_finish=lambda s: s.set(FLAG_MET_TA2),
            )
        if chapter == 1:
            return DialogueScript(
                speaker="Lena (TA)",
                lines=[
                    "You're not a loser. You're just lost.",
                    "Go do one small brave thing. Then another.",
                ],
            )
        if chapter >= 3 and state.has(FLAG_CULT_STOLE_CREDIT):
            return DialogueScript(
                speaker="Lena (TA)",
                lines=[
                    "They stole the rescue story. I know.",
                    "Don't burn yourself out trying to prove the truth. We'll help you show it.",
                ],
            )
        if chapter >= 8 and state.has(FLAG_FOUND_ARROWHEAD_MAP):
            return DialogueScript(
                speaker="Lena (TA)",
                lines=[
                    "So it's really on the other side of the world...",
                    "Promise me you won't fight the Children alone.",
                ],
            )
        return DialogueScript(speaker="Lena (TA)", lines=["Guild politics are messy. Keep your compass internal."])

    if npc_id == "rival":
        if chapter < 4:
            return None
        if state.has(FLAG_RIVAL_KIDNAPPED) and not state.has(FLAG_RIVAL_RESCUED):
            return DialogueScript(
                speaker="Rival",
                lines=[
                    "(Your rival is nowhere to be found.)",
                    f"A note reads: '{CHILDREN_OF_THE_NEPHIL} send their regards.'",
                ],
            )
        if state.has(FLAG_RIVAL_RESCUED):
            return DialogueScript(
                speaker="Rival",
                lines=[
                    "…I owe you one. Don't get used to hearing that.",
                    "Those 'Children' weren't rescuers. They were hunting.",
                ],
            )
        return DialogueScript(
            speaker="Rival",
            lines=[
                "Look who it is. Professor's favorite.",
                "Let's make it interesting: missions, relics, rescues. Whoever does more wins.",
                "Try to keep up, {player}.",
            ],
        )

    return None
