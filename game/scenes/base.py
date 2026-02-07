from __future__ import annotations

from abc import ABC, abstractmethod

import pygame


class Scene(ABC):
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> "Scene | None":
        raise NotImplementedError

    @abstractmethod
    def update(self, dt: float) -> "Scene | None":
        raise NotImplementedError

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

