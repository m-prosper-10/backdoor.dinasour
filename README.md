# Dino Runner Deluxe

An endless runner inspired by the Chrome dinosaur game, rebuilt as a polished desktop demo with Python and Pygame. The project is safe for classroom use: it runs locally, saves only local settings/progress, and includes a startup notice plus a cleanup/reset script.

## Features

- Endless runner gameplay with jumping, ducking, responsive controls, and stable delta-time updates
- Procedural retro visuals with day/night transitions, multiple biomes, particles, and challenge waves
- Flying enemies, cactus hazards, coins, combo streaks, and five power-up types
- Multiple unlockable dinosaur skins
- Start menu, tutorial, settings menu, pause screen, game over screen, fullscreen toggle, and scalable window
- Local JSON save data for high score, achievements, and unlocked skins
- Dependency checker and required-asset checker before game launch
- Safe optional demo shortcut creation for classroom demonstrations

## Safe Demo Notes

What is actually implemented:

- Local save data in the user's app-data folder
- Optional local launcher shortcut creation with `--create-demo-shortcut`
- Cleanup script to remove local save/config files and the optional demo shortcut

What is not implemented:

- No malware behavior
- No hidden installs
- No real persistence or startup registration
- No shell access, remote access, networking, or stealth behavior

The optional demo shortcut is only a local launcher file stored in the game's app-data folder. It does not auto-run and does not touch the system startup folder.

## Project Structure

```text
cybersec-game/
├── assets/
│   └── data/
│       ├── achievements.json
│       ├── biomes.json
│       ├── skins.json
│       └── tutorial.json
├── dino_runner/
│   ├── __init__.py
│   ├── __main__.py
│   ├── assets.py
│   ├── audio.py
│   ├── bootstrap.py
│   ├── constants.py
│   ├── effects.py
│   ├── entities.py
│   ├── game.py
│   ├── paths.py
│   ├── storage.py
│   ├── ui.py
│   └── world.py
├── cleanup_reset.py
├── main.py
├── README.md
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run From Source

```bash
python main.py
```

Optional classroom demo shortcut creation:

```bash
python main.py --create-demo-shortcut
```

If `pygame` or required local asset files are missing, the game shows a setup message and exits safely.

## Controls

- `Space`, `Up`, `W`: jump
- `Down`, `S`, `Left Ctrl`: duck / fast fall
- `P` or `Esc`: pause during gameplay
- `F11`: toggle fullscreen
- `M`: mute toggle
- Menu buttons can also be clicked with the mouse

## Save Data

The game stores JSON files in a local user folder:

- Windows: `%APPDATA%\DinoRunnerDeluxe`
- macOS/Linux: `~/.dino_runner_deluxe`

Saved data includes:

- `settings.json`
- `save_data.json`
- optional `demo_shortcuts/` launcher files

## Cleanup / Reset

To remove local settings, save data, and any optional demo shortcut:

```bash
python cleanup_reset.py
```

## Build A Windows Executable With PyInstaller

Use the exact command below from the project root on Windows:

```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name DinoRunnerDeluxe --add-data "assets;assets" main.py
```

Notes:

- `--windowed` builds a GUI executable without a console window.
- `--onefile` produces a single `.exe`.
- `--add-data "assets;assets"` bundles the JSON data assets so the helper path logic can still find them inside the packaged app.
- For a debug build with a console window, remove `--windowed`.

After building, the executable will be created under `dist\DinoRunnerDeluxe.exe`.

## How Asset Loading Works

The game uses `dino_runner.paths.resource_root()` and `asset_path()` to resolve files correctly in both cases:

- normal Python execution
- PyInstaller bundled mode using `sys._MEIPASS`

That means the same code works from source and from the packaged executable, as long as the `assets` folder is included with `--add-data`.

## Packaging Checklist

1. Install dependencies with `pip install -r requirements.txt`
2. Run the game once from source
3. Build with the PyInstaller command above
4. Test the generated executable from `dist\`
5. If you want a clean reset afterwards, run `python cleanup_reset.py`
