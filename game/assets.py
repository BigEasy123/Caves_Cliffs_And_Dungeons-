from __future__ import annotations

from pathlib import Path

import pygame


def try_load_sprite(path: str | Path, *, size: tuple[int, int]) -> pygame.Surface | None:
    """
    Best-effort image loader. Returns None if the file doesn't exist or can't be loaded.
    """
    p = Path(path)
    if not p.exists():
        return None
    try:
        image = pygame.image.load(str(p)).convert_alpha()
    except Exception:
        return None
    return pygame.transform.smoothscale(image, size)

