#!/usr/bin/env python3
"""
Launcher script for running the optimized version of the Temporal Maze game.
This version includes performance improvements to address freezing issues.
"""

import os
import sys
import traceback

# Display version information
print("Python version:", sys.version)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"Project root: {project_root}")

# Check for dependencies
try:
    print("Checking dependencies...")
    import pygame
    print(f"Pygame version: {pygame.version.ver}")
    
    import numpy
    print(f"NumPy version: {numpy.__version__}")
    
    print("All dependencies found!")
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please install required dependencies:")
    print("    pip install pygame numpy")
    sys.exit(1)

def main():
    """Run the optimized version of the game."""
    try:
        # Initialize pygame
        pygame.init()
        pygame.display.init()
        
        print("Pygame initialized successfully")
        print(f"Available display modes: {pygame.display.list_modes()}")
        
        # Import the optimized game class
        from src.game_enhanced.optimized_game import OptimizedGame
        
        # Initialize the optimized game
        print("Creating game instance...")
        game = OptimizedGame()
        
        # Run the game with the improved game loop
        print("Starting game loop...")
        game.run()
        
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        print("\nTry running with:")
        print("    python check_and_run.py")
        sys.exit(1)

if __name__ == "__main__":
    main() 