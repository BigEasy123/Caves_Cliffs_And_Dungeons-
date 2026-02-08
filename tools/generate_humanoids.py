from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Palette:
    skin: tuple[int, int, int]
    hair: tuple[int, int, int]
    shirt: tuple[int, int, int]
    pants: tuple[int, int, int]
    outline: tuple[int, int, int] = (0, 0, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate simple humanoid sprites (4-way + walk frames) into assets/sprites/")
    parser.add_argument("--tile", type=int, default=32, help="Frame size (default: 32)")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--variants", type=int, default=6, help="Number of generic NPC variants to generate")
    args = parser.parse_args()

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    pygame.init()
    try:
        pygame.display.set_mode((1, 1))
    except Exception:
        pass

    sprites = Path("assets/sprites")
    npcs = sprites / "npcs"
    sprites.mkdir(parents=True, exist_ok=True)
    npcs.mkdir(parents=True, exist_ok=True)

    # Player (Indy-ish palette)
    player_pal = Palette(skin=(210, 170, 140), hair=(60, 40, 25), shirt=(170, 120, 60), pants=(50, 60, 85))
    _write_set(sprites, "player", player_pal, tile=args.tile, overwrite=args.overwrite)

    # NPCs keyed by id for determinism/variety
    npc_ids = [
        "mayor",
        "archivist",
        "professor",
        "guard",
        "scout",
        "guild_clerk",
        "guild_captain",
        "guild_quartermaster",
    ]
    for npc_id in npc_ids:
        pal = _palette_from_id(npc_id)
        _write_set(npcs, npc_id, pal, tile=args.tile, overwrite=args.overwrite)

    # Generic variants for quick swapping / future NPCs
    for i in range(args.variants):
        npc_id = f"npc{i}"
        pal = _palette_from_id(npc_id)
        _write_set(npcs, npc_id, pal, tile=args.tile, overwrite=args.overwrite)

    pygame.quit()
    print("OK: generated humanoid sprite sets in assets/sprites/ and assets/sprites/npcs/")
    return 0


def _write_set(out_dir: Path, base: str, pal: Palette, *, tile: int, overwrite: bool) -> None:
    import pygame

    # Idle
    for d in ("down", "up", "left", "right"):
        p = out_dir / f"{base}_{d}.png"
        if p.exists() and not overwrite:
            continue
        surf = pygame.Surface((tile, tile), pygame.SRCALPHA)
        _draw_humanoid(surf, pal, facing=d, phase=0)
        pygame.image.save(surf, str(p))

    # Walk cycle (3 frames) per direction
    for d in ("down", "up", "left", "right"):
        for phase in range(3):
            p = out_dir / f"{base}_walk{phase}_{d}.png"
            if p.exists() and not overwrite:
                continue
            surf = pygame.Surface((tile, tile), pygame.SRCALPHA)
            _draw_humanoid(surf, pal, facing=d, phase=phase)
            pygame.image.save(surf, str(p))

    # Back-compat fallback file
    legacy = out_dir / f"{base}.png"
    if (not legacy.exists()) or overwrite:
        surf = pygame.Surface((tile, tile), pygame.SRCALPHA)
        _draw_humanoid(surf, pal, facing="down", phase=0)
        pygame.image.save(surf, str(legacy))


def _draw_humanoid(surf, pal: Palette, *, facing: str, phase: int) -> None:
    import pygame

    w, h = surf.get_size()
    cx = w // 2

    bob = 0 if phase == 0 else (-1 if phase == 1 else 0)
    leg = 1 if phase == 1 else (-1 if phase == 2 else 0)
    arm = -leg

    # Facing tweaks
    eye_offset = 0
    if facing == "left":
        eye_offset = -2
    elif facing == "right":
        eye_offset = 2

    # Head
    pygame.draw.circle(surf, pal.skin, (cx, 9 + bob), 5)
    # Hair cap
    pygame.draw.circle(surf, pal.hair, (cx, 8 + bob), 5, 2)
    # Eyes only for left/right/down
    if facing != "up":
        pygame.draw.circle(surf, (0, 0, 0), (cx + eye_offset - 1, 8 + bob), 1)
        pygame.draw.circle(surf, (0, 0, 0), (cx + eye_offset + 2, 8 + bob), 1)

    # Torso
    pygame.draw.rect(surf, pal.shirt, pygame.Rect(cx - 5, 14 + bob, 10, 9), 0, 2)
    pygame.draw.rect(surf, pal.outline, pygame.Rect(cx - 5, 14 + bob, 10, 9), 2, 2)

    # Arms (swing for walk)
    if facing in ("left", "right"):
        # One arm visible more
        pygame.draw.rect(surf, pal.skin, pygame.Rect(cx - 8, 15 + bob, 3, 7), 0, 2)
        pygame.draw.rect(surf, pal.skin, pygame.Rect(cx + 5, 15 + bob, 3, 7), 0, 2)
    elif facing == "up":
        pygame.draw.rect(surf, pal.skin, pygame.Rect(cx - 7, 16 + bob, 14, 3), 0, 2)
    else:
        pygame.draw.rect(surf, pal.skin, pygame.Rect(cx - 8, 15 + bob + arm, 3, 7), 0, 2)
        pygame.draw.rect(surf, pal.skin, pygame.Rect(cx + 5, 15 + bob - arm, 3, 7), 0, 2)

    # Pants
    pygame.draw.rect(surf, pal.pants, pygame.Rect(cx - 5, 22 + bob, 10, 6), 0, 2)
    pygame.draw.rect(surf, pal.outline, pygame.Rect(cx - 5, 22 + bob, 10, 6), 2, 2)

    # Legs
    if facing == "up":
        pygame.draw.rect(surf, pal.pants, pygame.Rect(cx - 4, 27 + bob, 3, 4), 0, 1)
        pygame.draw.rect(surf, pal.pants, pygame.Rect(cx + 1, 27 + bob, 3, 4), 0, 1)
    else:
        pygame.draw.rect(surf, pal.pants, pygame.Rect(cx - 4 + leg, 27 + bob, 3, 4), 0, 1)
        pygame.draw.rect(surf, pal.pants, pygame.Rect(cx + 1 - leg, 27 + bob, 3, 4), 0, 1)
    pygame.draw.rect(surf, pal.outline, pygame.Rect(cx - 4 + leg, 27 + bob, 3, 4), 1, 1)
    pygame.draw.rect(surf, pal.outline, pygame.Rect(cx + 1 - leg, 27 + bob, 3, 4), 1, 1)


def _palette_from_id(key: str) -> Palette:
    # Deterministic but varied colors from a string key.
    h = 2166136261
    for ch in key.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF

    def pick(a: int, b: int, c: int) -> int:
        nonlocal h
        h = (h * 1103515245 + 12345) & 0x7FFFFFFF
        return a + (h % (b - a + 1)) + c

    skin = (pick(185, 215, 0), pick(140, 190, 0), pick(120, 170, 0))
    hair = (pick(30, 90, 0), pick(20, 70, 0), pick(10, 55, 0))
    shirt = (pick(70, 190, 0), pick(60, 180, 0), pick(50, 170, 0))
    pants = (pick(30, 90, 0), pick(40, 110, 0), pick(60, 140, 0))
    return Palette(skin=skin, hair=hair, shirt=shirt, pants=pants)


if __name__ == "__main__":
    raise SystemExit(main())
