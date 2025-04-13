"""
Main entry point for the enhanced Temporal Maze game.
"""

from .optimized_game import OptimizedGame

def main():
    """Main entry point for the game."""
    # Initialize and run the game with the optimized version
    game = OptimizedGame()
    game.run()

if __name__ == "__main__":
    # Add the parent directory to sys.path to allow importing from src
    import os
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    main() 