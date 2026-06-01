#!/usr/bin/env python3
"""One-click launcher for the game.

Double-click this file or run it with Python to open the game automatically.
This still requires Python and the project's dependencies to be installed on
the recipient's machine.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        import arcade
    except ImportError:
        print("Missing dependency: arcade")
        print("Install it with: python3 -m pip install -r requirements.txt")
        return 1

    from game import MediterraneanJourney

    MediterraneanJourney()
    arcade.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
