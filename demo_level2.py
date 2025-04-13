#!/usr/bin/env python3

import os
import sys
import time

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from game_logic.world import World
from game_logic.player import Player
from game_logic.time_travel import TimeManager

def main():
    """
    Demonstration of Temporal Maze level 2 with multiple clones.
    """
    print("TEMPORAL MAZE LEVEL 2 DEMO")
    print("==========================")
    print("\nThis demonstration shows how multiple time clones can be used to solve more complex puzzles.\n")
    
    # Load the second level
    map_path = os.path.join('maps', 'level2.txt')
    world = World(map_path)
    
    # Create a player with a different starting position for level 2
    player = Player(3, 3)
    
    # Create time manager with 3 clone limit
    time_manager = TimeManager(max_clones=3)
    
    # Initial state
    print("Initial state:")
    print(world.render_map(player.get_position()))
    time.sleep(1)
    
    # Move to first switch
    print("\nPlayer moving to first switch...")
    moves = [(0, 0), (-1, 0), (0, 0)]  # Adjusted for new starting position
    
    for dx, dy in moves:
        player.move(dx, dy, world)
        print(world.render_map(player.get_position()))
        time.sleep(0.5)
    
    print("\nPlayer is now on the first switch.")
    
    # Create first clone
    print("\nCreating first clone to stay on switch 1...")
    time_manager.create_clone(player, 3)
    
    # Move to second switch
    print("\nPlayer moving to second switch...")
    moves = [(1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0)]
    
    for dx, dy in moves:
        player.move(dx, dy, world)
        clone_positions = time_manager.get_clone_positions()
        time_manager.update_clones(world)
        print(world.render_map(player.get_position(), clone_positions))
        time.sleep(0.3)
    
    print("\nPlayer is now on the second switch.")
    
    # Create second clone
    print("\nCreating second clone to stay on switch 2...")
    time_manager.create_clone(player, 3)
    
    # Move down through first door
    print("\nPlayer moving through the first door...")
    moves = [(0, 1), (0, 1), (0, 1), (0, 1)]
    
    for dx, dy in moves:
        player.move(dx, dy, world)
        clone_positions = time_manager.get_clone_positions()
        time_manager.update_clones(world)
        print(world.render_map(player.get_position(), clone_positions))
        time.sleep(0.3)
    
    # Move to third switch
    print("\nPlayer moving to third switch...")
    moves = [(0, 1), (0, 1), (-1, 0), (-1, 0), (-1, 0), (-1, 0), (-1, 0)]
    
    for dx, dy in moves:
        player.move(dx, dy, world)
        clone_positions = time_manager.get_clone_positions()
        time_manager.update_clones(world)
        print(world.render_map(player.get_position(), clone_positions))
        time.sleep(0.3)
    
    print("\nPlayer is now on the third switch.")
    
    # Create third clone
    print("\nCreating third clone to stay on switch 3...")
    time_manager.create_clone(player, 3)
    
    # Move to exit
    print("\nPlayer moving to the exit with all three doors open...")
    moves = [(1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0)]
    
    for dx, dy in moves:
        player.move(dx, dy, world)
        clone_positions = time_manager.get_clone_positions()
        time_manager.update_clones(world)
        print(world.render_map(player.get_position(), clone_positions))
        time.sleep(0.3)
    
    print("\nSuccess! Player reached the exit with the help of three time clones.")
    print("Each clone is pressing a different switch to keep all the doors open.")
    
    print("\nTo play the full game with interactive controls, run:")
    print("  python src/main.py")

if __name__ == "__main__":
    main() 