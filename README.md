# Caves_Cliffs_And_Dungeons-
A game that is a blend of Indy Jones and Pokemon mystery dungeon.

## Run
1. `python -m pip install -r requirements.txt`
2. `python main.py`

## Assets / Audio
- See `docs/ASSETS.md` for the drop-in folder structure (sprites, tile textures, and music).
- See `docs/DATA.md` for adding/editing items, enemies, and missions via JSON.

## Controls
- Title: `Enter` start adventure, `P` platformer prototype, `Esc` quit
- Home: `WASD`/arrows move, walk onto door to exit, `I` status, `Esc` title
- Town: `WASD`/arrows move, `E` talk, walk onto building doors/exits to travel, `I` status, `Esc` title
- Outskirts: `WASD`/arrows move, walk onto exit/gate, `I` status, `Esc` title
- Dungeon: `WASD`/arrows move (turn-based), walk into enemies to attack, `E` stairs/exit (bottom only), `I` inventory, `K` skills, `M` minimap, `R` regenerate
- Dialogue: `Enter`/`E` next, `Esc` close
- Shop: `Tab` buy/sell, `Enter`/`E` confirm, `Esc` back
- Guild: `Enter`/`E` accept/turn-in mission, `Esc` back
- Status: `I` open/close (gold + items)
- Inventory: `B` open (equip/use/drop)
- Saves: `F5/F6/F7` save slots 1-3, `F9/F10/F11` load slots 1-3, `F8` reset

## Project layout
- `main.py`: entry point
- `game/`: new scaffolding (app loop, scenes, dungeon gen)
- `prototype/`: old experiments kept runnable
- `assets/`: optional sprites/audio
