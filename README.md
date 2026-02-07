# Caves_Cliffs_And_Dungeons-
A game that is a blend of Indy Jones and Pokemon mystery dungeon.

## Run
1. `python -m pip install -r requirements.txt`
2. `python main.py`

## Controls
- Title: `Enter` start adventure, `P` platformer prototype, `Esc` quit
- Home: `WASD`/arrows move, `E` exit at door, `M` World Map, `Esc` title
- Town: `WASD`/arrows move, `E` talk/enter buildings/exit, `I` status, `Esc` title
- World Map: `1` home, `2` town, `3` dungeon, `4` dungeon, `Esc` title
- Dungeon: `WASD`/arrows move (turn-based), walk into enemies to attack, `E` use stairs, `I` inventory, `R` regenerate, `Esc` World Map
- Dialogue: `Enter`/`E` next, `Esc` close
- Shop: `Tab` buy/sell, `Enter`/`E` confirm, `Esc` back
- Guild: `Enter`/`E` accept mission, `Esc` back
- Status: `I` open/close (gold + items)

## Project layout
- `main.py`: entry point
- `game/`: new scaffolding (app loop, scenes, dungeon gen)
- `prototype/`: old experiments kept runnable
- `assets/`: optional sprites/audio
