from __future__ import annotations

import argparse
import math
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Colors:
    bg: tuple[int, int, int]
    fg: tuple[int, int, int]
    outline: tuple[int, int, int] = (0, 0, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate placeholder PNG tiles/sprites + WAV SFX into ./assets")
    parser.add_argument("--tile", type=int, default=32, help="Tile size in pixels (default: 32)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--labels", action="store_true", help="Draw text labels on tiles/sprites (default: off)")
    args = parser.parse_args()

    root = Path("assets")
    sprites = root / "sprites"
    tiles = sprites / "tiles"
    sfx = root / "sfx"
    sprites.mkdir(parents=True, exist_ok=True)
    tiles.mkdir(parents=True, exist_ok=True)
    sfx.mkdir(parents=True, exist_ok=True)

    _generate_pngs(tile_size=args.tile, tiles_dir=tiles, sprites_dir=sprites, overwrite=args.overwrite, labels=args.labels)
    _generate_sfx(sfx_dir=sfx, overwrite=args.overwrite)
    print("OK: generated placeholder assets in ./assets")
    return 0


def _generate_pngs(*, tile_size: int, tiles_dir: Path, sprites_dir: Path, overwrite: bool, labels: bool) -> None:
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    import pygame

    pygame.init()
    # Ensure surfaces work in headless contexts.
    try:
        pygame.display.set_mode((1, 1))
    except Exception:
        pass

    def tile(path: Path, label: str, colors: Colors, *, texture: str, icon: str | None = None, variant: int = 0) -> None:
        if path.exists() and not overwrite:
            return
        surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        surf.fill(colors.bg)
        pygame.draw.rect(surf, colors.outline, pygame.Rect(0, 0, tile_size, tile_size), 2)

        _draw_texture(surf, texture, colors, variant=variant)
        if icon is not None:
            _draw_icon(surf, icon, colors.fg)
        if labels:
            _draw_label(surf, label, (235, 235, 240))
        pygame.image.save(surf, str(path))

    def sprite(path: Path, label: str, colors: Colors, icon: str) -> None:
        if path.exists() and not overwrite:
            return
        surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, colors.bg, pygame.Rect(2, 2, tile_size - 4, tile_size - 4))
        pygame.draw.rect(surf, colors.outline, pygame.Rect(2, 2, tile_size - 4, tile_size - 4), 2)
        _draw_texture(surf, icon, colors, variant=1)
        _draw_icon(surf, icon, colors.fg)
        if labels:
            _draw_label(surf, label, (245, 245, 245))
        pygame.image.save(surf, str(path))

    tile(tiles_dir / "floor.png", "FLOOR", Colors((35, 38, 46), (60, 66, 78)), texture="dots", icon=None, variant=0)
    tile(tiles_dir / "wall.png", "WALL", Colors((80, 90, 110), (40, 45, 60)), texture="bricks", icon=None, variant=2)
    tile(tiles_dir / "door.png", "DOOR", Colors((190, 150, 90), (90, 60, 30)), texture="door", icon="door", variant=3)
    tile(tiles_dir / "stairs_up.png", "UP", Colors((170, 230, 150), (30, 90, 40)), texture="up", icon="up", variant=4)
    tile(tiles_dir / "stairs_down.png", "DOWN", Colors((120, 160, 230), (30, 60, 120)), texture="down", icon="down", variant=5)
    tile(tiles_dir / "shop.png", "SHOP", Colors((120, 180, 240), (20, 60, 120)), texture="bag", icon="bag", variant=6)
    tile(tiles_dir / "guild.png", "GUILD", Colors((240, 200, 120), (120, 80, 30)), texture="shield", icon="shield", variant=7)
    tile(tiles_dir / "healer.png", "HEAL", Colors((150, 240, 160), (40, 120, 60)), texture="plus", icon="plus", variant=8)
    tile(tiles_dir / "temple.png", "GATE", Colors((160, 210, 250), (30, 70, 120)), texture="temple", icon="temple", variant=9)
    tile(tiles_dir / "jungle.png", "GATE", Colors((140, 240, 180), (20, 120, 70)), texture="leaf", icon="leaf", variant=10)
    tile(tiles_dir / "exit.png", "EXIT", Colors((240, 230, 120), (120, 90, 20)), texture="star", icon="star", variant=11)
    tile(tiles_dir / "bed_tl.png", "BED", Colors((170, 120, 210), (80, 40, 120)), texture="bed_tl", icon="bed_tl", variant=12)
    tile(tiles_dir / "bed_tr.png", "BED", Colors((170, 120, 210), (80, 40, 120)), texture="bed_tr", icon="bed_tr", variant=13)
    tile(tiles_dir / "bed_bl.png", "BED", Colors((170, 120, 210), (80, 40, 120)), texture="bed_bl", icon="bed_bl", variant=14)
    tile(tiles_dir / "bed_br.png", "BED", Colors((170, 120, 210), (80, 40, 120)), texture="bed_br", icon="bed_br", variant=15)

    # Variants for themed dungeons / nicer towns (no labels by default).
    for i in range(1, 4):
        tile(tiles_dir / f"floor_stone{i}.png", f"STONE{i}", Colors((40, 44, 52), (70, 76, 88)), texture="bricks", icon=None, variant=20 + i)
        tile(tiles_dir / f"wall_rock{i}.png", f"ROCK{i}", Colors((70, 78, 96), (34, 38, 50)), texture="bricks", icon=None, variant=30 + i)
        tile(tiles_dir / f"wall_stone{i}.png", f"WSTONE{i}", Colors((85, 92, 110), (45, 50, 62)), texture="bricks", icon=None, variant=60 + i)
        tile(tiles_dir / f"floor_grass{i}.png", f"GRASS{i}", Colors((34, 62, 38), (60, 120, 70)), texture="leaf", icon=None, variant=40 + i)
        tile(tiles_dir / f"floor_gravel{i}.png", f"GRAVEL{i}", Colors((60, 56, 48), (110, 105, 95)), texture="dots", icon=None, variant=50 + i)
        tile(tiles_dir / f"floor_mud{i}.png", f"MUD{i}", Colors((78, 58, 38), (130, 95, 60)), texture="dots", icon=None, variant=70 + i)

    sprite(sprites_dir / "player.png", "YOU", Colors((240, 210, 80), (110, 80, 20)), icon="person")
    sprite(sprites_dir / "enemy.png", "FOE", Colors((220, 90, 90), (110, 30, 30)), icon="skull")

    pygame.quit()


def _draw_label(surf, text: str, color: tuple[int, int, int]) -> None:
    import pygame

    font = pygame.font.SysFont(None, 14)
    t = font.render(text, True, color)
    rect = t.get_rect(center=(surf.get_width() // 2, surf.get_height() - 8))
    surf.blit(t, rect.topleft)


def _draw_icon(surf, icon: str, color: tuple[int, int, int]) -> None:
    import pygame

    w, h = surf.get_size()
    cx, cy = w // 2, h // 2 - 2

    if icon == "dots":
        for y in range(7, h - 10, 6):
            for x in range(7, w - 6, 6):
                pygame.draw.circle(surf, color, (x, y), 1)
        return
    if icon == "bricks":
        for y in range(4, h - 12, 6):
            offset = 0 if (y // 6) % 2 == 0 else 4
            for x in range(4 + offset, w - 4, 8):
                pygame.draw.rect(surf, color, pygame.Rect(x, y, 6, 4), 0, 1)
        return
    if icon == "door":
        pygame.draw.rect(surf, color, pygame.Rect(cx - 6, cy - 8, 12, 16), 0, 2)
        pygame.draw.circle(surf, (240, 240, 240), (cx + 3, cy), 1)
        return
    if icon == "up":
        pygame.draw.polygon(surf, color, [(cx, cy - 10), (cx - 10, cy + 8), (cx + 10, cy + 8)])
        return
    if icon == "down":
        pygame.draw.polygon(surf, color, [(cx - 10, cy - 8), (cx + 10, cy - 8), (cx, cy + 10)])
        return
    if icon == "plus":
        pygame.draw.rect(surf, color, pygame.Rect(cx - 2, cy - 10, 4, 20))
        pygame.draw.rect(surf, color, pygame.Rect(cx - 10, cy - 2, 20, 4))
        return
    if icon == "bag":
        pygame.draw.rect(surf, color, pygame.Rect(cx - 8, cy - 4, 16, 14), 0, 2)
        pygame.draw.arc(surf, color, pygame.Rect(cx - 6, cy - 10, 12, 12), math.pi, 2 * math.pi, 2)
        return
    if icon == "shield":
        pygame.draw.polygon(surf, color, [(cx, cy - 12), (cx - 10, cy - 4), (cx - 6, cy + 10), (cx, cy + 14), (cx + 6, cy + 10), (cx + 10, cy - 4)])
        return
    if icon == "temple":
        pygame.draw.polygon(surf, color, [(cx, cy - 12), (cx - 14, cy - 2), (cx + 14, cy - 2)])
        pygame.draw.rect(surf, color, pygame.Rect(cx - 12, cy - 2, 24, 14), 0, 2)
        for x in (-8, 0, 8):
            pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(cx + x - 2, cy + 2, 4, 10))
        return
    if icon == "leaf":
        pygame.draw.ellipse(surf, color, pygame.Rect(cx - 11, cy - 8, 22, 16))
        pygame.draw.line(surf, (0, 0, 0), (cx - 9, cy + 6), (cx + 9, cy - 6), 2)
        return
    if icon == "star":
        pts = [
            (cx, cy - 12),
            (cx + 4, cy - 2),
            (cx + 14, cy - 2),
            (cx + 6, cy + 4),
            (cx + 10, cy + 14),
            (cx, cy + 8),
            (cx - 10, cy + 14),
            (cx - 6, cy + 4),
            (cx - 14, cy - 2),
            (cx - 4, cy - 2),
        ]
        pygame.draw.polygon(surf, color, pts)
        return
    if icon == "person":
        pygame.draw.circle(surf, color, (cx, cy - 8), 5)
        pygame.draw.rect(surf, color, pygame.Rect(cx - 6, cy - 2, 12, 14), 0, 2)
        return
    if icon == "skull":
        pygame.draw.circle(surf, color, (cx, cy - 4), 10)
        pygame.draw.rect(surf, color, pygame.Rect(cx - 8, cy + 4, 16, 8), 0, 2)
        pygame.draw.circle(surf, (0, 0, 0), (cx - 4, cy - 6), 2)
        pygame.draw.circle(surf, (0, 0, 0), (cx + 4, cy - 6), 2)
        return
    if icon.startswith("bed_"):
        import pygame

        w, h = surf.get_size()
        # Solid bed as a 2x2 sprite split across tiles.
        frame = color
        top = icon.endswith("_tl") or icon.endswith("_tr")
        left = icon.endswith("_tl") or icon.endswith("_bl")
        right = icon.endswith("_tr") or icon.endswith("_br")
        bottom = icon.endswith("_bl") or icon.endswith("_br")

        # Fill
        pygame.draw.rect(surf, frame, pygame.Rect(1, 1, w - 2, h - 2), 0, 3)

        # Border only on outer edges (so the 2x2 looks like one object)
        border = (0, 0, 0)
        if top:
            pygame.draw.line(surf, border, (1, 1), (w - 2, 1), 2)
        if bottom:
            pygame.draw.line(surf, border, (1, h - 2), (w - 2, h - 2), 2)
        if left:
            pygame.draw.line(surf, border, (1, 1), (1, h - 2), 2)
        if right:
            pygame.draw.line(surf, border, (w - 2, 1), (w - 2, h - 2), 2)
        return


def _draw_texture(surf, icon: str, colors: Colors, *, variant: int) -> None:
    import pygame
    import random

    w, h = surf.get_size()

    # Deterministic "noise" based on pixel position + variant.
    def jitter(x: int, y: int) -> int:
        v = (x * 928371 + y * 364479 + variant * 15485863) & 0xFFFFFFFF
        v ^= (v >> 13)
        v = (v * 1274126177) & 0xFFFFFFFF
        return (v >> 24) & 0xFF

    def shade(c: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
        return (max(0, min(255, c[0] + delta)), max(0, min(255, c[1] + delta)), max(0, min(255, c[2] + delta)))

    # Floor: speckle
    if icon in ("dots",):
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                n = jitter(x, y)
                if n < 18:
                    surf.set_at((x, y), shade(colors.bg, 12))
                elif n > 245:
                    surf.set_at((x, y), shade(colors.bg, -10))
        return

    # Wall: mottled stone
    if icon in ("bricks", "temple"):
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                n = jitter(x, y)
                if n < 8:
                    surf.set_at((x, y), shade(colors.bg, 18))
                elif n > 250:
                    surf.set_at((x, y), shade(colors.bg, -14))
        return

    # Jungle/grass: wispy blades
    if icon == "leaf":
        rng = random.Random((variant * 1000003 + w * 31 + h * 17) & 0xFFFFFFFF)
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                n = jitter(x, y)
                # Sparse light/dark specks
                if n < 10:
                    surf.set_at((x, y), shade(colors.bg, 16))
                elif n > 250:
                    surf.set_at((x, y), shade(colors.bg, -12))

        # Blades (thin, slightly angled lines) to make it read as "wispy grass".
        blade_count = 26 + (variant % 9)
        for _ in range(blade_count):
            x0 = 2 + rng.randrange(max(1, w - 4))
            y0 = h - 3 - rng.randrange(0, 4)
            length = rng.randrange(max(6, h // 3), h - 4)
            sway = rng.uniform(-0.9, 0.9)
            x1 = int(max(2, min(w - 3, x0 + sway * (length / 2))))
            y1 = max(2, y0 - length)

            main = shade(colors.bg, rng.choice([14, 18, 22]))
            pygame.draw.aaline(surf, main, (x0, y0), (x1, y1))

            if rng.random() < 0.45:
                hi = shade(colors.bg, 30)
                pygame.draw.aaline(surf, hi, (x0 + 1, y0), (min(w - 3, x1 + 1), y1))
        return

    # Doors / special: subtle diagonal
    if icon in ("door", "bag", "shield", "plus", "up", "down", "star", "person", "skull"):
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                if (x - y + variant) % 9 == 0:
                    surf.set_at((x, y), shade(colors.bg, 10))
        return


def _generate_sfx(*, sfx_dir: Path, overwrite: bool) -> None:
    sample_rate = 44100

    def write_beep(path: Path, *, freq: float, ms: int, volume: float = 0.35, slide: float = 0.0) -> None:
        if path.exists() and not overwrite:
            return
        n = int(sample_rate * (ms / 1000.0))
        frames = bytearray()
        for i in range(n):
            t = i / sample_rate
            f = freq + slide * (i / max(1, n - 1))
            # Simple envelope
            a = min(1.0, i / (sample_rate * 0.01))
            d = min(1.0, (n - 1 - i) / (sample_rate * 0.03))
            env = a * d
            s = math.sin(2.0 * math.pi * f * t) * volume * env
            v = int(max(-1.0, min(1.0, s)) * 32767)
            frames += int(v).to_bytes(2, byteorder="little", signed=True)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(frames)

    write_beep(sfx_dir / "hit.wav", freq=220, ms=120, volume=0.45, slide=-80)
    write_beep(sfx_dir / "pickup.wav", freq=880, ms=90, volume=0.35, slide=140)
    write_beep(sfx_dir / "door.wav", freq=330, ms=140, volume=0.35, slide=40)
    write_beep(sfx_dir / "confirm.wav", freq=660, ms=90, volume=0.30, slide=0)
    write_beep(sfx_dir / "shoot.wav", freq=520, ms=90, volume=0.30, slide=-120)
    write_beep(sfx_dir / "heal.wav", freq=740, ms=160, volume=0.30, slide=60)

    # Extra UI/feedback sounds
    write_beep(sfx_dir / "step.wav", freq=180, ms=45, volume=0.20, slide=0)
    write_beep(sfx_dir / "ui_open.wav", freq=860, ms=120, volume=0.28, slide=120)
    write_beep(sfx_dir / "ui_close.wav", freq=740, ms=110, volume=0.26, slide=-120)
    write_beep(sfx_dir / "error.wav", freq=190, ms=170, volume=0.32, slide=-30)
    write_beep(sfx_dir / "equip.wav", freq=540, ms=90, volume=0.28, slide=80)
    write_beep(sfx_dir / "mission.wav", freq=520, ms=240, volume=0.30, slide=260)


if __name__ == "__main__":
    raise SystemExit(main())
