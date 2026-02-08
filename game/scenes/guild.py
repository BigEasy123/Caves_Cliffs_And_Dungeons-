import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.story.missions import MISSIONS, apply_turn_in_rewards, is_turn_in_available
from game.ui.dialogue_box import DialogueBox
from game.ui.status_menu import StatusMenu
from game.items import ITEMS, get_item
from game.story.flags import (
    FLAG_ARROW_TIP_LOST,
    FLAG_CHILDREN_EXPERIMENT_SUCCEEDED,
    FLAG_FOUND_ARROWHEAD_MAP,
    FLAG_BOW_DESTROYED,
    FLAG_BOW_STOLEN,
    FLAG_CULT_STOLE_CREDIT,
    FLAG_MET_RECRUIT,
    FLAG_POSTGAME_UNLOCKED,
    FLAG_RIVAL_KIDNAPPED,
    FLAG_RIVAL_RESCUED,
)
from game.story.factions import CHILDREN_OF_THE_NEPHIL


class GuildScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.app.audio.play_music(PATHS.music / "town.ogg", volume=0.45)
        self.font_title = pygame.font.SysFont(None, 42)
        self.font = pygame.font.SysFont(None, 24)
        self.index = 0
        self.message = ""
        self.status_menu = StatusMenu()
        self.status_open = False
        self.dialogue = DialogueBox()
        self.dialogue_lines: list[str] | None = None
        self.dialogue_speaker = "Guild"
        self.dialogue_on_finish = None
        self.dialogue_index = 0

    def _play_cutscene(self, event_id: str) -> bool:
        from game.scenes.cutscene import CutsceneScene
        from game.story.cutscenes import cutscene_for_event

        cs = cutscene_for_event(event_id)
        if cs is None or STATE.has(cs.flag):
            return False
        STATE.set(cs.flag)
        self.app.set_scene(CutsceneScene(self.app, pages=cs.pages, next_scene=GuildScene(self.app)))
        return True

    def _reward_lines(self, mission_id: str, *, before_rank: int, before_chapter: int) -> list[str]:
        mission = MISSIONS[mission_id]
        xp = int(getattr(mission, "reward_guild_xp", 0))
        mission_type = str(getattr(mission, "mission_type", "misc"))

        opener_by_type = {
            "bounty": "Bounty confirmed. The board's getting quieter.",
            "rescue": "They're safe. That's what matters.",
            "escort": "Report received. Notes filed. Trails mapped.",
            "misc": "Work logged.",
        }
        lines: list[str] = [opener_by_type.get(mission_type, "Work logged.")]

        parts: list[str] = [f"+{int(getattr(mission, 'reward_gold', 0))}g"]
        if xp:
            parts.append(f"+{xp} guild XP")

        rewards_items = dict(getattr(mission, "reward_items", {}) or {})
        if rewards_items:
            for item_id, count in sorted(rewards_items.items()):
                name = get_item(item_id).name if item_id in ITEMS else str(item_id)
                parts.append(f"{name} x{int(count)}")

        after_rank = int(getattr(STATE, "guild_rank", 1))
        after_chapter = int(getattr(STATE, "chapter", 1))
        if after_rank > int(before_rank):
            parts.append(f"Rank up! {after_rank}")
        if after_chapter > int(before_chapter):
            parts.append(f"Chapter {after_chapter} unlocked")

        lines.append("Rewards: " + ", ".join(parts))
        return lines

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.status_open:
                self.status_open = False
                self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
                return None
            if self.dialogue_lines is not None:
                self._close_dialogue()
                return None
            board = str(getattr(STATE, "mission_board", "guild"))
            if board == "ice_camp":
                from game.scenes.base_camp import BaseCampScene

                return BaseCampScene(self.app)
            from game.scenes.town import TownScene

            return TownScene(self.app)

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            self.app.audio.play_sfx(
                PATHS.sfx / ("ui_open.wav" if self.status_open else "ui_close.wav"),
                volume=0.35,
            )
            return None

        if self.status_open:
            return None

        if self.dialogue_lines is not None:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e, pygame.K_SPACE):
                self._advance_dialogue()
            return None

        missions = self._available_missions()
        if not missions:
            return None

        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(missions)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(missions)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            mission_id = missions[self.index]
            if is_turn_in_available(STATE, mission_id):
                self._start_dialogue(
                    speaker="Guild Clerk",
                    lines=MISSIONS[mission_id].turn_in_lines,
                    on_finish=lambda: self._turn_in(mission_id),
                )
            elif mission_id in STATE.completed_missions:
                mission = MISSIONS.get(mission_id)
                if mission is not None and bool(getattr(mission, "repeatable", False)):
                    # Allow replay: clear completion/claim markers and re-accept.
                    STATE.completed_missions.discard(mission_id)
                    STATE.claimed_missions.discard(mission_id)
                    STATE.active_mission = mission_id
                    STATE.mission_kill_baseline = dict(STATE.kill_log)
                    self._start_dialogue(speaker="Guild Clerk", lines=mission.accept_lines)
                else:
                    self.message = "Already completed."
            else:
                STATE.active_mission = mission_id
                # Baseline bounty counters so kill-based missions progress from acceptance.
                STATE.mission_kill_baseline = dict(STATE.kill_log)
                if mission_id == "rival_hostage":
                    STATE.set(FLAG_RIVAL_KIDNAPPED)
                self._start_dialogue(speaker="Guild Clerk", lines=MISSIONS[mission_id].accept_lines)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        board = str(getattr(STATE, "mission_board", "guild"))
        title_text = "Guild" if board == "guild" else "Base Camp Board"
        title = self.font_title.render(title_text, True, COLOR_TEXT)
        surface.blit(title, (40, 50))

        header = self.font.render("Up/Down select  Enter/E accept  Esc back", True, COLOR_TEXT)
        surface.blit(header, (40, 95))

        y = 135
        missions = self._available_missions()
        if not missions:
            none = self.font.render("No missions available.", True, COLOR_TEXT)
            surface.blit(none, (40, y))
        else:
            for idx, mission_id in enumerate(missions[:12]):
                mission = MISSIONS[mission_id]
                prefix = "> " if idx == self.index else "  "
                active = " (ACTIVE)" if STATE.active_mission == mission_id else ""
                if is_turn_in_available(STATE, mission_id):
                    status = " (TURN IN)"
                elif mission_id in STATE.completed_missions:
                    status = " (DONE)"
                else:
                    status = ""
                line = self.font.render(f"{prefix}{mission.name}{active}{status}", True, COLOR_TEXT)
                surface.blit(line, (40, y))
                y += 26

            if 0 <= self.index < len(missions):
                mission = MISSIONS[missions[self.index]]
                desc = self.font.render(mission.description, True, (200, 200, 210))
                surface.blit(desc, (40, 450))

        if self.message:
            msg = self.font.render(self.message, True, (220, 190, 120))
            surface.blit(msg, (40, 420))

        if self.status_open:
            self.status_menu.draw(surface, STATE)

        if self.dialogue_lines is not None:
            self.dialogue.draw(surface, speaker=self.dialogue_speaker, line=self.dialogue_lines[self.dialogue_index])

    def _available_missions(self) -> list[str]:
        # Show all missions up to current chapter; completed-but-unclaimed remain visible as TURN IN.
        ids: list[str] = []
        for mission_id, mission in MISSIONS.items():
            if int(getattr(mission, "min_chapter", 1)) <= int(getattr(STATE, "chapter", 1)):
                board = str(getattr(mission, "board", "guild"))
                if str(getattr(STATE, "mission_board", "guild")) != board:
                    continue
                ids.append(mission_id)
        ids.sort(key=lambda mid: (int(getattr(MISSIONS[mid], "min_chapter", 1)), MISSIONS[mid].name))
        return ids

    def _start_dialogue(self, *, speaker: str, lines: list[str], on_finish=None) -> None:
        self.dialogue_speaker = speaker
        self.dialogue_lines = lines if lines else ["..."]
        self.dialogue_index = 0
        self.dialogue_on_finish = on_finish

    def _advance_dialogue(self) -> None:
        if self.dialogue_lines is None:
            return
        self.dialogue_index += 1
        if self.dialogue_index < len(self.dialogue_lines):
            return
        on_finish = self.dialogue_on_finish
        self._close_dialogue()
        if on_finish is not None:
            on_finish()

    def _close_dialogue(self) -> None:
        self.dialogue_lines = None
        self.dialogue_on_finish = None
        self.dialogue_index = 0

    def _turn_in(self, mission_id: str) -> None:
        before_rank = STATE.guild_rank
        before_chapter = STATE.chapter
        ok = apply_turn_in_rewards(STATE, mission_id)
        if ok:
            # New flow: always show a reward dialogue, then (optionally) a story cutscene.
            before_rank_i = int(before_rank)
            before_chapter_i = int(before_chapter)

            mission = MISSIONS[mission_id]
            self.message = f"Turned in: {mission.name}"
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)

            post_event: str | None = None

            if mission_id == "cave_in_rescue":
                STATE.set(FLAG_CULT_STOLE_CREDIT)
                STATE.hp = max(1, min(STATE.hp, max(1, STATE.max_hp_total() // 2)))
                post_event = "ch3_betrayal"
            elif mission_id == "rival_hostage":
                STATE.set(FLAG_RIVAL_RESCUED)
                STATE.unset(FLAG_RIVAL_KIDNAPPED)
                post_event = "ch4_rescue"
            elif mission_id == "nimrods_bow_find":
                STATE.set(FLAG_BOW_STOLEN)
                STATE.set(FLAG_MET_RECRUIT)
                post_event = "ch5_theft"
            elif mission_id == "nimrods_bow_destroy":
                STATE.set(FLAG_BOW_DESTROYED)
                STATE.set(FLAG_ARROW_TIP_LOST)
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 7)
                post_event = "chapter_7"
            elif mission_id == "ice_arrowhead_map":
                STATE.set(FLAG_FOUND_ARROWHEAD_MAP)
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 8)
                STATE.mission_board = "guild"
                post_event = "chapter_8"
            elif mission_id == "tropic_arrowhead":
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 9)
                post_event = "chapter_9"
            elif mission_id == "core_finale":
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 10)
                STATE.set(FLAG_POSTGAME_UNLOCKED)
                STATE.set(FLAG_CHILDREN_EXPERIMENT_SUCCEEDED)
                post_event = "chapter_10"

            after_chapter_i = int(getattr(STATE, "chapter", 1))
            if post_event is None and after_chapter_i > before_chapter_i:
                post_event = f"chapter_{after_chapter_i}"

            reward_lines = self._reward_lines(mission_id, before_rank=before_rank_i, before_chapter=before_chapter_i)

            def after_rewards() -> None:
                if post_event is not None:
                    self._play_cutscene(post_event)

            self._start_dialogue(speaker="Guild Clerk", lines=reward_lines, on_finish=after_rewards)
            return

            mission = MISSIONS[mission_id]
            xp = int(getattr(mission, "reward_guild_xp", 0))
            parts = [f"Rewards: +{mission.reward_gold}g"]
            if xp:
                parts.append(f"+{xp} guild XP")
            if STATE.guild_rank > before_rank:
                parts.append(f"Rank up! {STATE.guild_rank}")
            if STATE.chapter > before_chapter:
                parts.append(f"Chapter {STATE.chapter} unlocked")
            self.message = " | ".join(parts)
            from game.assets_manifest import PATHS

            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)

            major_beats = {
                "cave_in_rescue",
                "rival_hostage",
                "nimrods_bow_find",
                "nimrods_bow_destroy",
                "ice_arrowhead_map",
                "tropic_arrowhead",
                "core_finale",
            }
            if mission_id not in major_beats and int(getattr(STATE, "chapter", 1)) > int(before_chapter):
                self._play_cutscene(f"chapter_{int(getattr(STATE, 'chapter', 1))}")
                return
            if mission_id == "cave_in_rescue":
                STATE.set(FLAG_CULT_STOLE_CREDIT)
                STATE.hp = max(1, min(STATE.hp, max(1, STATE.max_hp_total() // 2)))
                self.message = f"{CHILDREN_OF_THE_NEPHIL} stole the credit. You were left bruised—and furious."
                self._play_cutscene("ch3_betrayal")
                return
            if mission_id == "rival_hostage":
                STATE.set(FLAG_RIVAL_RESCUED)
                STATE.unset(FLAG_RIVAL_KIDNAPPED)
                self._play_cutscene("ch4_rescue")
                return
            if mission_id == "nimrods_bow_find":
                # Part I climax: bow stolen, recruit vanishes.
                STATE.set(FLAG_BOW_STOLEN)
                STATE.set(FLAG_MET_RECRUIT)
                self._play_cutscene("ch5_theft")
                return
            if mission_id == "nimrods_bow_destroy":
                STATE.set(FLAG_BOW_DESTROYED)
                STATE.set(FLAG_ARROW_TIP_LOST)
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 7)
                self._play_cutscene("chapter_7")
                return
                self._start_dialogue(
                    speaker="Professor",
                    lines=[
                        "Good. It's over... mostly.",
                        "When the bow shattered, a single tip refused to burn—like the world itself wouldn't let it vanish.",
                        "We've lost it in a land of ice.",
                        f"And {CHILDREN_OF_THE_NEPHIL} will chase it. So will we.",
                        "Head to the Outskirts gate. An Ice Expedition Base Camp is being established.",
                    ],
                )
                return
            if mission_id == "ice_arrowhead_map":
                STATE.set(FLAG_FOUND_ARROWHEAD_MAP)
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 8)
                STATE.mission_board = "guild"
                self._play_cutscene("chapter_8")
                return
                self._start_dialogue(
                    speaker="Professor",
                    lines=[
                        "This map... it points to the arrow tip—across the world.",
                        "Pack light. We race the Children from this moment on.",
                        "Chapter 8 begins: Around the World.",
                    ],
                )
                return
            if mission_id == "tropic_arrowhead":
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 9)
                self._play_cutscene("chapter_9")
                return
                self._start_dialogue(
                    speaker="Professor",
                    lines=[
                        "You have it. The arrow tip.",
                        "The trail doesn't end—it dives. The Children are moving underground.",
                        "Chapter 9 begins: Journey to the Core.",
                    ],
                )
                return
            if mission_id == "core_finale":
                STATE.chapter = max(int(getattr(STATE, "chapter", 1)), 10)
                STATE.set(FLAG_POSTGAME_UNLOCKED)
                STATE.set(FLAG_CHILDREN_EXPERIMENT_SUCCEEDED)
                self._play_cutscene("chapter_10")
                return
                self._start_dialogue(
                    speaker="Professor",
                    lines=[
                        "The Children fell into their own trap.",
                        "Whatever wrath swallowed the Nephil has stirred again... and then went quiet.",
                        "Now comes the part no one teaches: what you do after the world doesn't end.",
                        "Do you go back to a normal life... or stay with the Guild?",
                        "(Either way, the Guild doors stay open to you.)",
                        "",
                        "One last report came in before we could breathe:",
                        "A single experiment of the Children of the Nephil worked.",
                        "We don't know what it made—only that it lived.",
                        "Cliffhanger logged. The next chapter of history is waiting.",
                    ],
                )
                return
        else:
            self.message = "You don't have the required items."

    def _after_cave_in_betrayal(self) -> None:
        STATE.set(FLAG_CULT_STOLE_CREDIT)
        STATE.hp = max(1, min(STATE.hp, max(1, STATE.max_hp_total() // 2)))
        self.message = f"{CHILDREN_OF_THE_NEPHIL} stole the credit. You were left bruised—and furious."
