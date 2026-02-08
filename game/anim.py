from __future__ import annotations

import pygame

from game.direction import Direction, direction_from_step


class StepAnimator:
    """
    Tiny helper for tile-step animation.
    Call `on_step()` whenever the entity moves one tile.
    """

    def __init__(self, frames: list[pygame.Surface], *, hold_ms: int = 180) -> None:
        self.frames = frames
        self.hold_ms = hold_ms
        self._index = 0
        self._until = 0

    def on_step(self) -> None:
        if not self.frames:
            return
        self._index = (self._index + 1) % len(self.frames)
        self._until = pygame.time.get_ticks() + self.hold_ms

    def current(self, fallback: pygame.Surface | None = None) -> pygame.Surface | None:
        if not self.frames:
            return fallback
        now = pygame.time.get_ticks()
        if now <= self._until:
            return self.frames[self._index]
        return fallback or self.frames[0]


class DirectionalStepAnimator:
    """
    Direction-aware variant of StepAnimator.
    - `frames_by_dir`: {Direction.DOWN: [..], Direction.UP: [..], ...}
    - Call `on_step(dx, dy)` to update direction and animate.
    """

    def __init__(self, frames_by_dir: dict[Direction, list[pygame.Surface]], *, hold_ms: int = 180) -> None:
        self.frames_by_dir = frames_by_dir
        self.hold_ms = hold_ms
        self.direction = Direction.DOWN
        self._index = 0
        self._until = 0

    def on_step(self, dx: int, dy: int) -> None:
        self.direction = direction_from_step(dx, dy, default=self.direction)
        frames = self.frames_by_dir.get(self.direction, [])
        if not frames:
            return
        self._index = (self._index + 1) % len(frames)
        self._until = pygame.time.get_ticks() + self.hold_ms

    def current(self, fallback_by_dir: dict[Direction, pygame.Surface] | None = None) -> pygame.Surface | None:
        frames = self.frames_by_dir.get(self.direction, [])
        fallback = None
        if fallback_by_dir is not None:
            fallback = fallback_by_dir.get(self.direction)
        if not frames:
            return fallback
        now = pygame.time.get_ticks()
        if now <= self._until:
            return frames[self._index]
        return fallback or frames[0]
