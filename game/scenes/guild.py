import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.story.missions import MISSIONS, apply_turn_in_rewards, is_turn_in_available
from game.ui.dialogue_box import DialogueBox
from game.ui.status_menu import StatusMenu
from game.story.flags import (
    FLAG_BOW_DESTROYED,
    FLAG_BOW_STOLEN,
    FLAG_CULT_STOLE_CREDIT,
    FLAG_MET_RECRUIT,
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
        title = self.font_title.render("Guild", True, COLOR_TEXT)
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
            if mission_id == "cave_in_rescue":
                self._start_dialogue(
                    speaker="Guild Clerk",
                    lines=[
                        "We should be celebrating... but listen.",
                        "Those 'rescuers' in red robes are already spinning the story.",
                        "They'll take credit. They'll call you a helper.",
                        "And if you protest... they'll make sure you can't.",
                        "(Later, outside the hall...)",
                        "A sharp pain catches you between the ribs. You hit the ground.",
                        "Voices laugh: 'History belongs to the strong.'",
                        f"When you wake, the town is cheering {CHILDREN_OF_THE_NEPHIL}'s 'heroic rescue'.",
                    ],
                    on_finish=self._after_cave_in_betrayal,
                )
            if mission_id == "rival_hostage":
                STATE.set(FLAG_RIVAL_RESCUED)
                STATE.unset(FLAG_RIVAL_KIDNAPPED)
                self._start_dialogue(
                    speaker="Guild Clerk",
                    lines=[
                        "You got them back. The medics are taking over.",
                        "Whatever you two had going on... let it go.",
                        f"{CHILDREN_OF_THE_NEPHIL} doesn't care about pride—only leverage.",
                    ],
                )
            if mission_id == "nimrods_bow_find":
                # Part I climax: bow stolen, recruit vanishes.
                STATE.set(FLAG_BOW_STOLEN)
                STATE.set(FLAG_MET_RECRUIT)
                self._start_dialogue(
                    speaker="Guild Clerk",
                    lines=[
                        "The bow... was on the table. Now it's gone.",
                        "The new recruit is gone too.",
                        f"A note is pinned to the door: '{CHILDREN_OF_THE_NEPHIL} claim what was always ours.'",
                        "Part I ends here. The fallout starts now.",
                    ],
                )
                return
            if mission_id == "nimrods_bow_destroy":
                STATE.set(FLAG_BOW_DESTROYED)
                self._start_dialogue(
                    speaker="Professor",
                    lines=[
                        "Good. It's over.",
                        "No relic. No leverage. No fracture point.",
                        f"But {CHILDREN_OF_THE_NEPHIL} will not forget what you did.",
                    ],
                )
                return
        else:
            self.message = "You don't have the required items."

    def _after_cave_in_betrayal(self) -> None:
        STATE.set(FLAG_CULT_STOLE_CREDIT)
        STATE.hp = max(1, min(STATE.hp, max(1, STATE.max_hp_total() // 2)))
        self.message = f"{CHILDREN_OF_THE_NEPHIL} stole the credit. You were left bruised—and furious."
