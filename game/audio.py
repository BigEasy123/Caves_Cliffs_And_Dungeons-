from __future__ import annotations

from pathlib import Path

import pygame


class Audio:
    def __init__(self) -> None:
        self.enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.enabled = True
        except Exception:
            self.enabled = False

        self._current_music: Path | None = None
        self._sfx_cache: dict[Path, pygame.mixer.Sound] = {}

    def play_music(self, path: str | Path, *, volume: float = 0.5, loop: bool = True) -> None:
        if not self.enabled:
            return
        p = Path(path)
        if not p.exists():
            return
        if self._current_music == p:
            return
        try:
            pygame.mixer.music.load(str(p))
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            pygame.mixer.music.play(-1 if loop else 0)
            self._current_music = p
        except Exception:
            pass

    def stop_music(self) -> None:
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self._current_music = None

    def play_sfx(self, path: str | Path, *, volume: float = 0.6) -> None:
        if not self.enabled:
            return
        p = Path(path)
        if not p.exists():
            return
        try:
            snd = self._sfx_cache.get(p)
            if snd is None:
                snd = pygame.mixer.Sound(str(p))
                self._sfx_cache[p] = snd
            snd.set_volume(max(0.0, min(1.0, volume)))
            snd.play()
        except Exception:
            pass
