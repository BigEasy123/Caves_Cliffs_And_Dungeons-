from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pickup:
    item_id: str
    x: int
    y: int
    amount: int = 1

