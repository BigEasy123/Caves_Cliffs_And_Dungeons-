from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameState:
    flags: set[str] = field(default_factory=set)

    def has(self, flag: str) -> bool:
        return flag in self.flags

    def set(self, flag: str) -> None:
        self.flags.add(flag)

    def unset(self, flag: str) -> None:
        self.flags.discard(flag)


STATE = GameState()

