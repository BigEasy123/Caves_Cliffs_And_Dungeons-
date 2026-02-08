## Assets overview

This project will run even with **no assets** (it falls back to colored rectangles and silence).
You can drop in art/audio at any time and the game will pick them up on next launch.

### Folder layout

```
assets/
  sprites/
    player.png          (optional)
    enemy.png           (optional)
    tiles/              (optional)
      floor.png
      wall.png
      door.png
      stairs_up.png
      stairs_down.png
      shop.png
      guild.png
      healer.png
      temple.png
      jungle.png
      exit.png
      bed_tl.png
      bed_tr.png
      bed_bl.png
      bed_br.png
      floor_stone1.png
      floor_stone2.png
      floor_stone3.png
      wall_rock1.png
      wall_rock2.png
      wall_rock3.png
      floor_grass1.png
      floor_grass2.png
      floor_grass3.png
      floor_gravel1.png
      floor_gravel2.png
      floor_gravel3.png
      floor_mud1.png
      floor_mud2.png
      floor_mud3.png
      wall_stone1.png
      wall_stone2.png
      wall_stone3.png
  music/                (optional)
    title.ogg
    home.ogg
    town.ogg
    world_map.ogg
    dungeon.ogg
  sfx/                  (optional)
    hit.wav
    pickup.wav
    door.wav
    confirm.wav
    shoot.wav
    heal.wav
    step.wav
    ui_open.wav
    ui_close.wav
    error.wav
    equip.wav
    mission.wav
```

### Visuals (sprites / tiles)

- **Recommended format:** PNG with transparency.
- **Tile size:** `32x32` (the engine will scale to the configured tile size).
- If a file is missing or fails to load, the game draws a simple colored shape instead.

Currently used paths:
- `assets/sprites/player.png`
- `assets/sprites/enemy.png`
- `assets/sprites/tiles/*.png` (see list above)

### Music

- Music is **optional** and loaded with `pygame.mixer.music`.
- Suggested format: `.ogg` (but any format supported by your installed SDL_mixer build should work).
- If audio init fails (common on some systems), the game continues without music.

Currently used tracks (optional):
- `assets/music/title.ogg`
- `assets/music/home.ogg`
- `assets/music/town.ogg`
- `assets/music/world_map.ogg`
- `assets/music/dungeon.ogg`

### Hotkeys for saves (handy when iterating)

- `F5/F6/F7`: save to `saves/save1.json` / `save2.json` / `save3.json`
- `F9/F10/F11`: load those slots
- `F8`: reset to a fresh game state

## Generating placeholders (no external tools)

If you don't want to use an art program yet, you can auto-generate a full set of placeholder
tiles/sprites and WAV SFX:

```bash
python tools/generate_placeholders.py --overwrite
```

This writes PNGs into `assets/sprites/` and `assets/sprites/tiles/`, and WAV files into `assets/sfx/`.

## Generating humanoid sprites + animation (no external tools)

You can also generate a simple human-like player sprite and a 3-frame walk cycle:

```bash
python tools/generate_humanoids.py --overwrite
```

Files written:
- Player (4-way idle + walk):
  - `assets/sprites/player_down.png`, `player_up.png`, `player_left.png`, `player_right.png`
  - `assets/sprites/player_walk0_down.png` ... `player_walk2_right.png`
- NPCs:
  - `assets/sprites/npcs/<npc_id>_down.png` (and `_up/_left/_right` + walk frames)
