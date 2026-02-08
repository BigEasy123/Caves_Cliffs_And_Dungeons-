from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from game.state import GameState, STATE


SAVE_VERSION = 2
DEFAULT_SAVE_PATH = Path("saves/save1.json")


def save_state(path: str | Path = DEFAULT_SAVE_PATH, state: GameState = STATE) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = _serialize_state(state)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_state(path: str | Path = DEFAULT_SAVE_PATH, state: GameState = STATE) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    payload = json.loads(p.read_text(encoding="utf-8"))
    _apply_state(state, payload)
    return True


def reset_state(state: GameState = STATE) -> None:
    state.flags.clear()
    state.gold = 50
    state.max_hp = 20
    state.hp = 20
    state.base_attack = 4
    state.base_defense = 0
    state.combat_level = 1
    state.combat_xp = 0
    state.guild_rank = 1
    state.guild_xp = 0
    state.chapter = 1
    state.inventory.clear()
    state.equipment = {"weapon": None, "armor": None, "trinket": None}
    state.completed_missions.clear()
    state.claimed_missions.clear()
    state.active_mission = None
    state.kill_log.clear()
    state.mission_kill_baseline.clear()
    state.guard_turns = 0
    state.poison_turns = 0
    state.poison_damage = 0


def save_slot(slot: int, state: GameState = STATE) -> None:
    save_state(Path(f"saves/save{slot}.json"), state=state)


def load_slot(slot: int, state: GameState = STATE) -> bool:
    return load_state(Path(f"saves/save{slot}.json"), state=state)


def _serialize_state(state: GameState) -> dict[str, Any]:
    d = asdict(state)
    d["flags"] = sorted(list(state.flags))
    d["completed_missions"] = sorted(list(state.completed_missions))
    d["claimed_missions"] = sorted(list(state.claimed_missions))
    return {"version": SAVE_VERSION, "state": d}


def _apply_state(state: GameState, payload: dict[str, Any]) -> None:
    version = int(payload.get("version", 0))
    if version != SAVE_VERSION:
        # Simple strategy for now: attempt best-effort load of common fields.
        pass

    data = payload.get("state", {})
    state.flags = set(data.get("flags", []))
    state.gold = int(data.get("gold", 50))
    state.max_hp = int(data.get("max_hp", 20))
    state.hp = int(data.get("hp", state.max_hp))
    state.base_attack = int(data.get("base_attack", 4))
    state.base_defense = int(data.get("base_defense", 0))
    state.combat_level = int(data.get("combat_level", 1))
    state.combat_xp = int(data.get("combat_xp", 0))
    state.guild_rank = int(data.get("guild_rank", 1))
    state.guild_xp = int(data.get("guild_xp", 0))
    state.chapter = int(data.get("chapter", max(1, min(10, state.guild_rank))))
    state.inventory = {str(k): int(v) for k, v in (data.get("inventory", {}) or {}).items()}
    equip = data.get("equipment", {}) or {}
    state.equipment = {"weapon": equip.get("weapon", None), "armor": equip.get("armor", None), "trinket": equip.get("trinket", None)}
    state.completed_missions = set(data.get("completed_missions", []))
    state.claimed_missions = set(data.get("claimed_missions", []))
    state.active_mission = data.get("active_mission", None)
    state.kill_log = {str(k): int(v) for k, v in (data.get("kill_log", {}) or {}).items()}
    state.mission_kill_baseline = {str(k): int(v) for k, v in (data.get("mission_kill_baseline", {}) or {}).items()}
    state.guard_turns = int(data.get("guard_turns", 0))
    state.poison_turns = int(data.get("poison_turns", 0))
    state.poison_damage = int(data.get("poison_damage", 0))

    # Clamp after load (handles max_hp bonus items, older saves, etc.)
    state.hp = max(0, min(state.hp, state.max_hp_total()))
