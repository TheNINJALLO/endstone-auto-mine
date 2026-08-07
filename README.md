# Endstone Auto-Mine Plugin

AFK auto-mining plugin for Endstone that allows tagged players to automatically mine a designated area using their equipped pickaxe.

## Features

- **Tag-gated access**: Requires `automine` player tag
- **Pickaxe required**: Must hold a pickaxe to start mining
- **Full enchantment support**:
  - **Silk Touch**: Drops the block itself
  - **Fortune**: Enhanced drops from ores
  - **Efficiency**: Faster mining speed
  - **Unbreaking**: Reduced durability loss
- **Durability tracking**: Stops automatically when pickaxe breaks
- **Layer-by-layer mining**: Top-down, efficient pattern

## Commands

| Command | Description |
|---------|-------------|
| `/automine <x1> <y1> <z1> <x2> <y2> <z2>` | Start mining the specified area |
| `/automine stop` | Stop current mining session |
| `/automine status` | Check mining progress |

### Example
```
/automine 100 60 200 150 40 250
```
This mines a 51x21x51 area from (100, 60, 200) to (150, 40, 250).

## Installation

1. Build the plugin:
   ```
   py -3.11 -m build
   ```

2. Copy the `.whl` file from `dist/` to your server's `plugins/` folder.

3. Restart/reload the server.

## Usage

1. Grant the `automine` tag to a player:
   ```
   /tag <player> add automine
   ```

2. Hold a pickaxe and run the automine command with coordinates.

3. Stay AFK while mining proceeds automatically.

## Requirements

- Endstone 0.11.8+
- Python 3.9+
