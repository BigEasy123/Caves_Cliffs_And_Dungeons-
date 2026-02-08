from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from game.data_loader import load_json


@dataclass(frozen=True)
class ItemDef:
    item_id: str
    name: str
    description: str
    buy_price: int = 0
    sell_price: int = 0
    type: str = "misc"
    usable_in_dungeon: bool = False
    slot: str | None = None
    stats: dict[str, int] | None = None
    effects: dict[str, int] | None = None


_DEFAULT_ITEMS: dict[str, ItemDef] = {
    "potion_small": ItemDef(
        item_id="potion_small",
        name="Small Potion",
        description="Heals 6 HP.",
        type="consumable",
        buy_price=15,
        sell_price=7,
        usable_in_dungeon=True,
        effects={"heal_hp": 6},
    ),
    "torch": ItemDef(
        item_id="torch",
        name="Torch",
        description="A basic torch. Useful in dark places (later).",
        type="utility",
        buy_price=10,
        sell_price=5,
    ),
    "relic_shard": ItemDef(
        item_id="relic_shard",
        name="Relic Shard",
        description="A fragment of an old carving. Valuable to the Guild/Archivist.",
        type="material",
        buy_price=0,
        sell_price=25,
    ),
    "whip": ItemDef(
        item_id="whip",
        name="Leather Whip",
        description="A trusty whip. +1 ATK when equipped.",
        type="weapon",
        buy_price=45,
        sell_price=20,
        slot="weapon",
        stats={"attack": 1},
    ),
    "jacket": ItemDef(
        item_id="jacket",
        name="Field Jacket",
        description="Rugged jacket. +1 DEF when equipped.",
        type="armor",
        buy_price=40,
        sell_price=18,
        slot="armor",
        stats={"defense": 1},
    ),
    "lucky_charm": ItemDef(
        item_id="lucky_charm",
        name="Lucky Charm",
        description="A worn charm. +2 Max HP when equipped.",
        type="trinket",
        buy_price=55,
        sell_price=25,
        slot="trinket",
        stats={"max_hp": 2},
    ),
}


def _items_from_json(data: dict[str, Any]) -> dict[str, ItemDef]:
    items: dict[str, ItemDef] = {}
    for item_id, raw in data.items():
        if not isinstance(raw, dict):
            continue
        items[item_id] = ItemDef(
            item_id=item_id,
            name=str(raw.get("name", item_id)),
            description=str(raw.get("description", "")),
            type=str(raw.get("type", "misc")),
            buy_price=int(raw.get("buy_price", 0)),
            sell_price=int(raw.get("sell_price", 0)),
            usable_in_dungeon=bool(raw.get("usable_in_dungeon", False)),
            slot=(str(raw["slot"]) if "slot" in raw and raw["slot"] is not None else None),
            stats=(raw.get("stats") if isinstance(raw.get("stats"), dict) else None),
            effects=(raw.get("effects") if isinstance(raw.get("effects"), dict) else None),
        )
    return items


ITEMS: dict[str, ItemDef] = _DEFAULT_ITEMS
_loaded = load_json("data/items.json")
if isinstance(_loaded, dict):
    parsed = _items_from_json(_loaded)
    if parsed:
        ITEMS = parsed


def get_item(item_id: str) -> ItemDef:
    return ITEMS[item_id]
