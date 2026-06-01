# Mediterranean Journey

**Group Members:** Giorgio, Andreas

## Description

This is a Python `arcade` game about the journey across the Mediterranean.

## Play

Run the game from Python:

```bash
python game.py
```

## Package For Mac And Windows

To let people download and play the game without VS Code, package it into a desktop app with PyInstaller.

Important:

- Build the Mac version on a Mac.
- Build the Windows version on a Windows machine.
- PyInstaller is not a cross-compiler, so one machine will not produce both native app types.

### 1. Set up the environment

Install the dependency and PyInstaller:

```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

### 2. Build a Mac app

On macOS, this creates a `.app` bundle inside `dist/`:

```bash
pyinstaller --noconfirm --windowed --name "Mediterranean Journey" game.py
```

If you want a single-file build instead of a folder, you can use:

```bash
pyinstaller --noconfirm --onefile --windowed --name "Mediterranean Journey" game.py
```

For distribution, the `.app` or the `dist/` folder can be zipped and uploaded.

### 3. Build a Windows app

On Windows, this creates an `.exe` in `dist/`:

```bash
pyinstaller --noconfirm --windowed --name "Mediterranean Journey" game.py
```

You can also use `--onefile` if you want a single executable:

```bash
pyinstaller --noconfirm --onefile --windowed --name "Mediterranean Journey" game.py
```

### 4. Publish it

The easiest places to publish a downloadable game are:

- GitHub Releases
- itch.io
- Google Drive or Dropbox for a private share

Upload the zipped Mac build and zipped Windows build separately, then give players the correct download for their system.

## Notes

- This project currently starts in fullscreen.
- Press `Esc` to quit.
- If you later add external assets like images or sounds, you may need to include them in the PyInstaller build with `--add-data`.

