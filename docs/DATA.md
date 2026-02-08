## Data-driven content (JSON)

This repo supports editing core content without changing Python code:

- `data/items.json` (items, equipment, consumables)
- `data/enemies.json` (enemy stats + behaviors)
- `data/missions.json` (missions, dialogue, objectives, rewards)

If a JSON file is missing or invalid, the game falls back to built-in defaults.

### Editing workflow

1. Edit the JSON file
2. Restart the game (`python main.py`)

### Tips

- Keep IDs stable (`potion_small`, `raider`, `relic_shard`, etc.)
- Prices are in gold.
- Equipment uses `type: weapon|armor` and `slot: weapon|armor` plus `stats`.

