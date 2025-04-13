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
    Simple demonstration of Temporal Maze game mechanics.
    """
    print("TEMPORAL MAZE DEMO")
    print("==================")
    print("\nThis demonstration shows the core mechanics of the game.")
    print("It will run through predefined moves to show how time travel works.\n")
    
    # Load the first level
    map_path = os.path.join('maps', 'level1.txt')
    world = World(map_path)
    
    # Create a player
    player = Player(2, 2)
    
    # Create time manager
    time_manager = TimeManager()
    
    # Initial state
    print("Initial state:")
    print(world.render_map(player.get_position()))
    time.sleep(1)
    
    # Series of moves to reach the switch
    print("\nPlayer moving toward the switch...")
    moves = [(0, 1), (0, 1), (1, 0), (1, 0), (1, 0), (0, -1)]
    
    for dx, dy in moves:
        player.move(dx, dy, world)
        print(world.render_map(player.get_position()))
        time.sleep(0.5)
    
    print("\nPlayer is now on the switch, which opens the door.")
    time.sleep(1)
    
    # Create a time clone to stay on the switch
    print("\nCreating a time clone to stay on the switch while player moves through the door...")
    time_manager.create_clone(player, 5)  # Create clone that goes back 5 steps
    
    # Move away from the switch
    player.move(0, 1, world)
    
    # Update clone positions
    for _ in range(6):  # Update several times to let clone move
        clone_positions = time_manager.get_clone_positions()
        time_manager.update_clones(world)
        print(world.render_map(player.get_position(), clone_positions))
        time.sleep(0.5)
    
    print("\nThe clone has replayed the player's movements and is now standing on the switch.")
    print("The door remains open, allowing the player to pass through.")
    
    # Player moves through door
    moves = [(0, 1), (0, 1), (0, 1)]
    for dx, dy in moves:
        player.move(dx, dy, world)
        clone_positions = time_manager.get_clone_positions()
        time_manager.update_clones(world)
        print(world.render_map(player.get_position(), clone_positions))
        time.sleep(0.5)
    
    # Player moves to exit
    moves = [(1, 0), (1, 0), (1, 0), (1, 0)]
    for dx, dy in moves:
        player.move(dx, dy, world)
        print(world.render_map(player.get_position(), time_manager.get_clone_positions()))
        time.sleep(0.5)
    
    print("\nPlayer has reached the exit! Level complete.")
    
    print("\nThis demonstrates the core mechanics of Temporal Maze:")
    print("1. Player movement")
    print("2. Switches that open doors")
    print("3. Time travel to create clones that repeat past movements")
    print("4. Using clones strategically to solve puzzles")
    
    print("\nTo play the full game with interactive controls, run:")
    print("  python src/main.py")

if __name__ == "__main__":
    main() 