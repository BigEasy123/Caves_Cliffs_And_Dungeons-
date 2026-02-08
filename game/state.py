from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameState:
    flags: set[str] = field(default_factory=set)
    player_name: str = ""
    gold: int = 50
    # Base stats (equipment bonuses are applied via helper methods).
    max_hp: int = 20
    hp: int = 20
    base_attack: int = 4
    base_defense: int = 0
    combat_level: int = 1
    combat_xp: int = 0
    guild_rank: int = 1
    guild_xp: int = 0
    chapter: int = 1
    mission_board: str = "guild"  # guild | ice_camp
    inventory: dict[str, int] = field(default_factory=dict)
    equipment: dict[str, str | None] = field(default_factory=lambda: {"weapon": None, "armor": None, "trinket": None})
    completed_missions: set[str] = field(default_factory=set)
    claimed_missions: set[str] = field(default_factory=set)
    active_mission: str | None = None
    kill_log: dict[str, int] = field(default_factory=dict)
    mission_kill_baseline: dict[str, int] = field(default_factory=dict)
    rescued_miners_total: int = 0
    missions_turned_in_total: int = 0
    relics_turned_in_total: int = 0
    rival_missions: int = 0
    rival_relics: int = 0
    rival_rescues: int = 0
    guard_turns: int = 0
    poison_turns: int = 0
    poison_damage: int = 0

    def rivalry_player_score(self) -> int:
        # Weight relics higher than routine missions.
        return int(self.missions_turned_in_total) + int(self.rescued_miners_total) + int(self.relics_turned_in_total) * 3

    def rivalry_rival_score(self) -> int:
        return int(self.rival_missions) + int(self.rival_rescues) + int(self.rival_relics) * 3

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

    def equip(self, slot: str, item_id: str | None) -> None:
        self.equipment[slot] = item_id

    @staticmethod
    def combat_xp_to_next(level: int) -> int:
        # Slightly increasing curve: 25, 40, 55, ...
        return max(10, 25 + max(0, level - 1) * 15)

    @staticmethod
    def guild_xp_to_next(rank: int) -> int:
        # Story progression is slower than combat leveling.
        return max(10, 40 + max(0, rank - 1) * 30)

    def add_combat_xp(self, amount: int) -> int:
        if amount <= 0:
            return 0
        self.combat_xp += amount
        gained = 0
        while self.combat_xp >= self.combat_xp_to_next(self.combat_level):
            self.combat_xp -= self.combat_xp_to_next(self.combat_level)
            self.combat_level += 1
            gained += 1
            # Small growth per level.
            self.max_hp += 2
            if self.combat_level % 2 == 0:
                self.base_attack += 1
            if self.combat_level % 4 == 0:
                self.base_defense += 1
            self.hp = min(self.hp, self.max_hp_total())
        return gained

    def add_guild_xp(self, amount: int) -> int:
        if amount <= 0:
            return 0
        self.guild_xp += amount
        gained = 0
        while self.guild_xp >= self.guild_xp_to_next(self.guild_rank) and self.guild_rank < 10:
            self.guild_xp -= self.guild_xp_to_next(self.guild_rank)
            self.guild_rank += 1
            gained += 1
            self.chapter = max(self.chapter, min(10, self.guild_rank))
        return gained

    def record_kill(self, enemy_id: str) -> None:
        self.kill_log[enemy_id] = int(self.kill_log.get(enemy_id, 0)) + 1

    def equipment_stat_bonus(self, stat: str) -> int:
        from game.items import ITEMS

        bonus = 0
        for _, item_id in (self.equipment or {}).items():
            if not item_id or item_id not in ITEMS:
                continue
            stats = ITEMS[item_id].stats or {}
            bonus += int(stats.get(stat, 0))
        return bonus

    def max_hp_total(self) -> int:
        return max(1, int(self.max_hp) + self.equipment_stat_bonus("max_hp"))

    def attack(self) -> int:
        return int(self.base_attack) + self.equipment_stat_bonus("attack")

    def defense(self) -> int:
        return int(self.base_defense) + self.equipment_stat_bonus("defense")


STATE = GameState()
