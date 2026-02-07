from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssetPaths:
    root: Path = Path("assets")
    sprites: Path = Path("assets/sprites")
    tiles: Path = Path("assets/sprites/tiles")
    music: Path = Path("assets/music")
    sfx: Path = Path("assets/sfx")


PATHS = AssetPaths()

