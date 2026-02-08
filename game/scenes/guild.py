import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.story.missions import MISSIONS, apply_turn_in_rewards, is_turn_in_available
from game.ui.dialogue_box import DialogueBox
from game.ui.status_menu import StatusMenu


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
                return None
            if self.dialogue_lines is not None:
                self._close_dialogue()
                return None
            from game.scenes.town import TownScene

            return TownScene(self.app)

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
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
        # Show all missions; completed-but-unclaimed remain visible as TURN IN.
        return list(MISSIONS.keys())

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
        ok = apply_turn_in_rewards(STATE, mission_id)
        if ok:
            mission = MISSIONS[mission_id]
            self.message = f"Rewards: +{mission.reward_gold}g"
            from game.assets_manifest import PATHS

            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
        else:
            self.message = "You don't have the required items."
