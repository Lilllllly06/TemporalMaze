#!/usr/bin/env python3
"""
Launcher script for running the enhanced Temporal Maze game from the project root.
Run this script from the project root to start the game.
"""

import os
import sys

# Add the project root to the Python path (this is the key fix)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the main function and run it directly 
# (we already set up the path correctly)
from src.game_enhanced.main import main

if __name__ == "__main__":
    main() 