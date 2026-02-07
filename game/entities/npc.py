from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Npc:
    npc_id: str
    name: str
    x: int
    y: int

