# Caves_Cliffs_And_Dungeons-
A game that is a blend of Indy Jones and Pokemon mystery dungeon.

## Run
1. `python -m pip install -r requirements.txt`
2. `python main.py`

## Assets / Audio
- See `docs/ASSETS.md` for the drop-in folder structure (sprites, tile textures, and music).

## Controls
- Title: `Enter` start adventure, `P` platformer prototype, `Esc` quit
- Home: `WASD`/arrows move, `E` exit to town, `I` status, `Esc` title
- Town: `WASD`/arrows move, `E` talk/enter buildings/exit, `I` status, `Esc` title
- Outskirts: `WASD`/arrows move, `E` enter dungeon / return to town, `I` status, `Esc` title
- Dungeon: `WASD`/arrows move (turn-based), walk into enemies to attack, `E` stairs/exit (bottom only), `I` inventory, `R` regenerate
- Dialogue: `Enter`/`E` next, `Esc` close
- Shop: `Tab` buy/sell, `Enter`/`E` confirm, `Esc` back
- Guild: `Enter`/`E` accept mission, `Esc` back
- Status: `I` open/close (gold + items)
- Saves: `F5` save, `F9` load, `F8` reset

## Project layout
- `main.py`: entry point
- `game/`: new scaffolding (app loop, scenes, dungeon gen)
- `prototype/`: old experiments kept runnable
- `assets/`: optional sprites/audio
