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


def load_sprite_variants(dir_path: str | Path, *, prefix: str, size: tuple[int, int]) -> list[pygame.Surface]:
    """
    Loads sprites like `{prefix}1.png`, `{prefix}2.png`, ... from a directory.
    Also accepts `{prefix}.png` as a single fallback.
    Missing files are ignored.
    """
    d = Path(dir_path)
    variants: list[pygame.Surface] = []

    single = try_load_sprite(d / f"{prefix}.png", size=size)
    if single is not None:
        variants.append(single)

    for idx in range(1, 21):
        surf = try_load_sprite(d / f"{prefix}{idx}.png", size=size)
        if surf is not None:
            variants.append(surf)

    return variants


def pick_variant(variants: list[pygame.Surface], *, x: int, y: int, seed: int) -> pygame.Surface | None:
    if not variants:
        return None
    idx = (x * 73856093 + y * 19349663 + seed * 83492791) % len(variants)
    return variants[idx]
