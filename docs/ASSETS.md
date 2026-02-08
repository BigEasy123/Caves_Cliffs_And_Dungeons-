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
  music/                (optional)
    title.ogg
    home.ogg
    town.ogg
    world_map.ogg
    dungeon.ogg
  sfx/                  (optional, not wired yet)
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

- `F5`: save to `saves/save.json`
- `F9`: load from `saves/save.json`
- `F8`: reset to a fresh game state
