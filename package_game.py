#!/usr/bin/env python3
"""Build a distributable version of the game with PyInstaller.

Run this on macOS to produce a `.app` bundle, and on Windows to produce a
Windows executable bundle. The script zips the finished app into `releases/`
so it is easy to upload to GitHub Releases, itch.io, or a file-sharing site.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
GAME_FILE = PROJECT_ROOT / "game.py"
APP_NAME = "Mediterranean Journey"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
RELEASES_DIR = PROJECT_ROOT / "releases"


def run_pyinstaller(onefile: bool) -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        str(GAME_FILE),
    ]

    if onefile:
        cmd.insert(cmd.index("--windowed"), "--onefile")

    if sys.platform == "darwin":
        cmd.extend(["--osx-bundle-identifier", "com.local.mediterraneanjourney"])

    subprocess.run(cmd, check=True)


def build_release_archive(onefile: bool) -> Path:
    RELEASES_DIR.mkdir(exist_ok=True)

    if sys.platform == "darwin":
        app_path = DIST_DIR / f"{APP_NAME}.app"
        if not app_path.exists():
            raise FileNotFoundError(f"Expected macOS app bundle not found: {app_path}")
        archive_base = RELEASES_DIR / f"{APP_NAME.replace(' ', '_')}_mac"
        archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=DIST_DIR, base_dir=f"{APP_NAME}.app")
        return Path(archive_path)

    if sys.platform == "win32":
        bundle_dir = DIST_DIR / APP_NAME
        exe_path = bundle_dir / f"{APP_NAME}.exe"
        if onefile:
            exe_path = DIST_DIR / f"{APP_NAME}.exe"
            if not exe_path.exists():
                raise FileNotFoundError(f"Expected Windows executable not found: {exe_path}")
            temp_dir = RELEASES_DIR / "_zip_temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(exe_path, temp_dir / exe_path.name)
            archive_base = RELEASES_DIR / f"{APP_NAME.replace(' ', '_')}_windows"
            archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=temp_dir, base_dir=exe_path.name)
            shutil.rmtree(temp_dir)
            return Path(archive_path)

        if not exe_path.exists():
            raise FileNotFoundError(f"Expected Windows app bundle not found: {exe_path}")
        archive_base = RELEASES_DIR / f"{APP_NAME.replace(' ', '_')}_windows"
        archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=DIST_DIR, base_dir=APP_NAME)
        return Path(archive_path)

    # Linux or other platforms: still package the generated dist folder.
    archive_base = RELEASES_DIR / f"{APP_NAME.replace(' ', '_')}_{platform.system().lower()}"
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=DIST_DIR, base_dir=APP_NAME)
    return Path(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a release package for the game.")
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Build a single-file executable instead of the default app bundle/folder.",
    )
    args = parser.parse_args()

    if not GAME_FILE.exists():
        raise FileNotFoundError(f"Missing game entry point: {GAME_FILE}")

    print(f"Building {APP_NAME} from {GAME_FILE.name}...")
    run_pyinstaller(args.onefile)

    archive_path = build_release_archive(args.onefile)
    print(f"Release package created at: {archive_path}")
    print("Upload that zip file to GitHub Releases, itch.io, or another download host.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
