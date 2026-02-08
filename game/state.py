from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameState:
    flags: set[str] = field(default_factory=set)
    gold: int = 50
    max_hp: int = 20
    hp: int = 20
    inventory: dict[str, int] = field(default_factory=dict)
    completed_missions: set[str] = field(default_factory=set)
    claimed_missions: set[str] = field(default_factory=set)
    active_mission: str | None = None

    def has(self, flag: str) -> bool:
        return flag in self.flags

    def set(self, flag: str) -> None:
        self.flags.add(flag)

    def unset(self, flag: str) -> None:
        self.flags.discard(flag)

    def add_item(self, item_id: str, amount: int = 1) -> None:
        if amount <= 0:
            return
        self.inventory[item_id] = self.inventory.get(item_id, 0) + amount

    def remove_item(self, item_id: str, amount: int = 1) -> bool:
        if amount <= 0:
            return True
        have = self.inventory.get(item_id, 0)
        if have < amount:
            return False
        remaining = have - amount
        if remaining <= 0:
            self.inventory.pop(item_id, None)
        else:
            self.inventory[item_id] = remaining
        return True

    def item_count(self, item_id: str) -> int:
        return self.inventory.get(item_id, 0)


STATE = GameState()
