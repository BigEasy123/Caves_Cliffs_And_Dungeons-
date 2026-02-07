from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ItemDef:
    item_id: str
    name: str
    description: str
    buy_price: int
    sell_price: int
    usable_in_dungeon: bool = False


ITEMS: dict[str, ItemDef] = {
    "potion_small": ItemDef(
        item_id="potion_small",
        name="Small Potion",
        description="Heals 6 HP.",
        buy_price=15,
        sell_price=7,
        usable_in_dungeon=True,
    ),
    "torch": ItemDef(
        item_id="torch",
        name="Torch",
        description="A basic torch. Useful in dark places (later).",
        buy_price=10,
        sell_price=5,
    ),
    "relic_shard": ItemDef(
        item_id="relic_shard",
        name="Relic Shard",
        description="A fragment of an old carving. Might be valuable to an archivist.",
        buy_price=0,
        sell_price=25,
    ),
}


def get_item(item_id: str) -> ItemDef:
    return ITEMS[item_id]

