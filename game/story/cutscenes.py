from __future__ import annotations

from dataclasses import dataclass

from game.scenes.cutscene import CutscenePage
from game.story.flags import (
    FLAG_SEEN_CH10_CUTSCENE,
    FLAG_SEEN_CH2_CUTSCENE,
    FLAG_SEEN_CH3_BETRAYAL_CUTSCENE,
    FLAG_SEEN_CH3_CUTSCENE,
    FLAG_SEEN_CH4_CUTSCENE,
    FLAG_SEEN_CH4_RESCUE_CUTSCENE,
    FLAG_SEEN_CH5_CUTSCENE,
    FLAG_SEEN_CH5_THEFT_CUTSCENE,
    FLAG_SEEN_CH6_CUTSCENE,
    FLAG_SEEN_CH7_CUTSCENE,
    FLAG_SEEN_CH8_CUTSCENE,
    FLAG_SEEN_CH9_CUTSCENE,
)


@dataclass(frozen=True)
class CutsceneDef:
    flag: str
    pages: list[CutscenePage]


def cutscene_for_event(event_id: str) -> CutsceneDef | None:
    """
    Event IDs:
      - chapter_2 ... chapter_10
      - ch3_betrayal
      - ch4_rescue
      - ch5_theft
    """
    event_id = str(event_id or "").strip().lower()

    if event_id == "chapter_2":
        return CutsceneDef(
            flag=FLAG_SEEN_CH2_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 2 â€” The Grand Search",
                    body=(
                        "You wake to a backpack that isn't yours.\n\n"
                        "Ren (TA) has labeled everything in neat ink: ROPE, TORCHES, WATER.\n"
                        "Lena (TA) adds one final item: a note that reads, \"EAT.\" (Underlined twice.)\n\n"
                        "The Professor clears his throat.\n"
                        "\"A lost civilization in the desert,\" he says. \"The Nephil. Mythic giants, pre-Flood.\n"
                        "Three relics. One truth.\n\n"
                        "And the Children of the Nephil already have boots in the sand.\""
                    ),
                ),
                CutscenePage(
                    title="Sand and Stories",
                    body=(
                        "Klaus Von Hoffman smirks.\n\n"
                        "\"Try not to die on your first real dig, {player}.\"\n\n"
                        "He says it like a joke.\n"
                        "But his eyes are measuring you like equipment."
                    ),
                ),
            ],
        )

    if event_id == "chapter_3":
        return CutsceneDef(
            flag=FLAG_SEEN_CH3_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 3 â€” Cave-in",
                    body=(
                        "A courier arrives breathless, snow in their hair and panic in their hands.\n\n"
                        "\"The mine collapsed,\" they say. \"People are trapped. Dozens.\"\n\n"
                        "The Professor is already moving.\n"
                        "Klaus is already arguing.\n"
                        "Ren and Lena are already packing.\n\n"
                        "You realize something strange:\n"
                        "You aren't being asked if you'll go.\n"
                        "You're being trusted to."
                    ),
                )
            ],
        )

    if event_id == "ch3_betrayal":
        return CutsceneDef(
            flag=FLAG_SEEN_CH3_BETRAYAL_CUTSCENE,
            pages=[
                CutscenePage(
                    title="The Credit",
                    body=(
                        "They cheer in the streets.\n"
                        "They clap for the wrong names.\n\n"
                        "The papers say the Children of the Nephil were heroes.\n"
                        "They say you helped.\n"
                        "They say that like it's the same thing.\n\n"
                        "Later, in the dark, pain blooms between your ribs.\n"
                        "A voice laughs: \"History belongs to the strong.\""
                    ),
                ),
                CutscenePage(
                    title="After",
                    body=(
                        "You wake with bruises you can't show and anger you can't put down.\n\n"
                        "The Guild tells you to rest.\n"
                        "Your body agrees.\n"
                        "Your mind doesn't.\n\n"
                        "From now on, you don't just rescue people.\n"
                        "You rescue the truth."
                    ),
                ),
            ],
        )

    if event_id == "chapter_4":
        return CutsceneDef(
            flag=FLAG_SEEN_CH4_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 4 â€” Rivalry",
                    body=(
                        "Klaus corners you in the Guild Hall like a lecture.\n\n"
                        "\"Missions. Relics. Rescues,\" he says.\n"
                        "\"Let's see what the Professor's favorite can do when it counts.\"\n\n"
                        "Ren winces. Lena rolls her eyes.\n"
                        "The Professor says nothing.\n\n"
                        "You tell yourself it's just competition.\n"
                        "Just momentum.\n"
                        "Justâ€”fun."
                    ),
                ),
                CutscenePage(
                    title="Scorekeeping",
                    body=(
                        "For a while, it is fun.\n\n"
                        "Then the Children start watching.\n"
                        "And rivalry stops being a game.\n"
                        "It becomes a map of your weaknesses."
                    ),
                ),
            ],
        )

    if event_id == "ch4_rescue":
        return CutsceneDef(
            flag=FLAG_SEEN_CH4_RESCUE_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Hostage",
                    body=(
                        "You find Klaus where the torchlight doesn't reach.\n"
                        "Pride bruised. Hands bound. The smugness gone.\n\n"
                        "\"Don't,\" he rasps, as if he's still giving orders.\n"
                        "\"Don't make this your victory.\""
                    ),
                ),
                CutscenePage(
                    title="Ally",
                    body=(
                        "Back in town, he doesn't thank you.\n"
                        "Not at first.\n\n"
                        "But later, quietly, he says:\n"
                        "\"You did the right thing.\"\n\n"
                        "And for Klaus Von Hoffman, that's a confession."
                    ),
                ),
            ],
        )

    if event_id == "chapter_5":
        return CutsceneDef(
            flag=FLAG_SEEN_CH5_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 5 â€” Not What They Seem (Part I)",
                    body=(
                        "The new recruit arrives smiling too easily.\n\n"
                        "Klaus calls them \"eager.\" Ren calls them \"nice.\" Lena calls them \"convenient.\"\n\n"
                        "Then a report comes in: a tower where languages donâ€™t belong together.\n"
                        "A structure that shouldnâ€™t exist.\n\n"
                        "The Professor says one word like a warning:\n"
                        "\"Babel.\""
                    ),
                )
            ],
        )

    if event_id == "ch5_theft":
        return CutsceneDef(
            flag=FLAG_SEEN_CH5_THEFT_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Stolen",
                    body=(
                        "The bow is on the table.\n"
                        "Then it isn't.\n\n"
                        "A note is pinned to the door:\n"
                        "\"We claim what was always ours.\"\n\n"
                        "The recruit is gone.\n"
                        "Trust goes with them."
                    ),
                )
            ],
        )

    if event_id == "chapter_6":
        return CutsceneDef(
            flag=FLAG_SEEN_CH6_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 6 â€” Not What They Seem (Part II)",
                    body=(
                        "The Professor doesnâ€™t raise his voice.\n"
                        "He doesnâ€™t need to.\n\n"
                        "\"We retrieve it,\" he says.\n"
                        "\"Then we destroy it.\n"
                        "No trophies. No debate.\""
                    ),
                )
            ],
        )

    if event_id == "chapter_7":
        return CutsceneDef(
            flag=FLAG_SEEN_CH7_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 7 â€” A New Land",
                    body=(
                        "The bow shatters.\n"
                        "A fragment refuses to burn.\n\n"
                        "It vanishes into ice and rumor.\n\n"
                        "Base Camp goes up in a day: canvas, wood, and urgency.\n"
                        "You can feel it in your teethâ€”this isnâ€™t a quest.\n"
                        "Itâ€™s containment."
                    ),
                )
            ],
        )

    if event_id == "chapter_8":
        return CutsceneDef(
            flag=FLAG_SEEN_CH8_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 8 â€” Around the World",
                    body=(
                        "The map points across the world.\n\n"
                        "Ren tries to make it sound exciting.\n"
                        "Lena tries to make it sound survivable.\n"
                        "Klaus tries to make it sound inevitable.\n\n"
                        "The Professor calls it what it is:\n"
                        "\"A race.\""
                    ),
                ),
                CutscenePage(
                    title="Island Heat",
                    body=(
                        "A tropical island. A volcano. The air tastes like salt and old ash.\n\n"
                        "Adventure, the way you imagined it as a kid.\n\n"
                        "Then you remember:\n"
                        "The Children are imagining it too.\n"
                        "And they donâ€™t care who burns."
                    ),
                ),
            ],
        )

    if event_id == "chapter_9":
        return CutsceneDef(
            flag=FLAG_SEEN_CH9_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 9 â€” Journey to the Core",
                    body=(
                        "The Children descend.\n"
                        "So do you.\n\n"
                        "Every step down feels older than stone.\n"
                        "Older than language.\n\n"
                        "The Flood ended the Nephil once.\n"
                        "If the Children wake that wrath againâ€¦\n"
                        "there may not be a second chance."
                    ),
                )
            ],
        )

    if event_id == "chapter_10":
        return CutsceneDef(
            flag=FLAG_SEEN_CH10_CUTSCENE,
            pages=[
                CutscenePage(
                    title="Chapter 10 â€” Retirement?",
                    body=(
                        "The world doesnâ€™t end with fireworks.\n\n"
                        "It ends with paperwork.\n"
                        "Bandages.\n"
                        "Quiet meals you donâ€™t finish.\n\n"
                        "The Professor asks you a question that hits harder than any blade:\n"
                        "\"What do you do after you survive?\""
                    ),
                ),
                CutscenePage(
                    title="Cliffhanger",
                    body=(
                        "The Guild keeps its doors open.\n"
                        "School keeps its doors open.\n"
                        "Your future opens like a corridor you can finally walk.\n\n"
                        "And somewhere, anonymously, patientlyâ€¦\n"
                        "the Childrenâ€™s one successful experiment breathes.\n\n"
                        "Waiting for the right time."
                    ),
                ),
            ],
        )

    return None

