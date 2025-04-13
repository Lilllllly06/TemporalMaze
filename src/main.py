#!/usr/bin/env python3

import os
import sys
import time
import curses
from game_logic.world import World
from game_logic.player import Player
from game_logic.time_travel import TimeManager

# Constants
STARTING_LEVEL = 1
PLAYER_START_X = 2
PLAYER_START_Y = 2
TIME_STEP_DELAY = 0.2  # seconds between game updates

# Initialize game state
game_over = False
level_completed = False
current_level = STARTING_LEVEL
message = ""

def initialize_game(level):
    """
    Initialize the game with the specified level.
    
    Args:
        level (int): Level number
        
    Returns:
        tuple: (world, player, time_manager)
    """
    # Load the world
    map_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"maps/level{level}.txt")
    world = World(map_path)
    
    # Create the player at a default starting position
    # In a more complex game, you'd read this from the map file
    player = Player(PLAYER_START_X, PLAYER_START_Y)
    
    # Create the time manager
    time_manager = TimeManager()
    
    return world, player, time_manager

def handle_input(key, player, world, time_manager):
    """
    Handle user input.
    
    Args:
        key (int): Key code
        player (Player): The player object
        world (World): The game world
        time_manager (TimeManager): The time manager
        
    Returns:
        tuple: (quit_game, message)
    """
    global game_over, level_completed, message
    
    # Check for game control keys
    if key == ord('q') or key == ord('Q'):
        return True, "Quitting game..."
    
    if key == ord('r') or key == ord('R'):
        return False, "Restarting level..."
    
    # Movement keys (arrow keys or WASD)
    if key in [curses.KEY_UP, ord('w'), ord('W')]:
        player.move(0, -1, world)
    elif key in [curses.KEY_DOWN, ord('s'), ord('S')]:
        player.move(0, 1, world)
    elif key in [curses.KEY_LEFT, ord('a'), ord('A')]:
        player.move(-1, 0, world)
    elif key in [curses.KEY_RIGHT, ord('d'), ord('D')]:
        player.move(1, 0, world)
    
    # Time travel key
    elif key in [ord('t'), ord('T')]:
        return False, "Enter steps back (1-50): "
    
    # Check if the player reached the exit
    x, y = player.get_position()
    if world.is_exit(x, y):
        level_completed = True
        return False, f"Level {current_level} completed!"
    
    return False, ""

def process_time_travel(steps_back, player, time_manager):
    """
    Process time travel request.
    
    Args:
        steps_back (int): Number of steps to go back
        player (Player): The player object
        time_manager (TimeManager): The time manager
        
    Returns:
        str: Result message
    """
    # Validate input
    try:
        steps = int(steps_back)
        if steps < 1 or steps > player.max_history:
            return f"Invalid steps. Must be between 1 and {player.max_history}."
        
        # Create the clone
        if time_manager.create_clone(player, steps):
            return f"Created time clone going back {steps} steps."
        else:
            return "Failed to create time clone. Too many clones active."
    except ValueError:
        return "Invalid input. Please enter a number."

def render_game(stdscr, world, player, time_manager, message=""):
    """
    Render the game on the screen.
    
    Args:
        stdscr (curses.window): The curses window
        world (World): The game world
        player (Player): The player object
        time_manager (TimeManager): The time manager
        message (str): Message to display
    """
    stdscr.clear()
    
    # Get terminal dimensions
    max_y, max_x = stdscr.getmaxyx()
    
    # Get the player and clone positions
    player_pos = player.get_position()
    clone_positions = time_manager.get_clone_positions()
    
    # Render the map
    map_string = world.render_map(player_pos, clone_positions)
    for i, line in enumerate(map_string.split('\n')):
        if i < max_y:  # Make sure we don't go past the screen height
            # Prevent writing to the last column of the screen which can cause errors
            if len(line) >= max_x:
                line = line[:max_x-1]
            try:
                stdscr.addstr(i, 0, line)
            except curses.error:
                # Catch any curses errors (e.g., writing to bottom-right corner)
                pass
    
    # Render game info (if there's room)
    info_start_y = min(world.height + 1, max_y - 6)
    if info_start_y < max_y:
        try:
            stdscr.addstr(info_start_y, 0, f"Level: {current_level}")
        except curses.error:
            pass
    
    if info_start_y + 1 < max_y:
        try:
            stdscr.addstr(info_start_y + 1, 0, f"Clones: {len(time_manager.clones)}/{time_manager.max_clones}")
        except curses.error:
            pass
    
    # Render message (if there's room)
    if info_start_y + 3 < max_y and message:
        try:
            # Truncate message if too long
            display_msg = message[:max_x-1] if len(message) >= max_x else message
            stdscr.addstr(info_start_y + 3, 0, display_msg)
        except curses.error:
            pass
    
    # Render controls (if there's room)
    if info_start_y + 5 < max_y:
        try:
            controls = "Controls: Arrow keys/WASD to move | T for time travel | R to restart | Q to quit"
            # Truncate controls if too long
            if len(controls) >= max_x:
                controls = controls[:max_x-1]
            stdscr.addstr(info_start_y + 5, 0, controls)
        except curses.error:
            pass
    
    stdscr.refresh()

def main(stdscr):
    """
    Main game function.
    
    Args:
        stdscr (curses.window): The curses window
    """
    global game_over, level_completed, current_level, message
    
    # Set up curses
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.timeout(100)  # Input timeout in ms
    
    # Check terminal size
    max_y, max_x = stdscr.getmaxyx()
    if max_y < 10 or max_x < 20:
        stdscr.addstr(0, 0, "Terminal too small")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Initialize the game
    world, player, time_manager = initialize_game(current_level)
    
    # Main game loop
    time_travel_mode = False
    time_travel_input = ""
    last_update = time.time()
    
    while not game_over:
        # Check if level is completed
        if level_completed:
            current_level += 1
            try:
                world, player, time_manager = initialize_game(current_level)
                level_completed = False
                message = f"Starting level {current_level}"
            except Exception as e:
                message = "Congratulations! You completed all levels!"
                render_game(stdscr, world, player, time_manager, message)
                stdscr.nodelay(False)
                stdscr.getch()  # Wait for a key press
                game_over = True
                continue
        
        # Handle input
        key = stdscr.getch()
        if key != -1:  # -1 means no key was pressed
            if time_travel_mode:
                if key == 27:  # ESC key
                    time_travel_mode = False
                    time_travel_input = ""
                    message = "Time travel canceled."
                elif key == 10 or key == 13:  # Enter key
                    message = process_time_travel(time_travel_input, player, time_manager)
                    time_travel_mode = False
                    time_travel_input = ""
                elif key in range(48, 58):  # Digits 0-9
                    time_travel_input += chr(key)
                    message = f"Enter steps back (1-50): {time_travel_input}"
                elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                    time_travel_input = time_travel_input[:-1]
                    message = f"Enter steps back (1-50): {time_travel_input}"
            else:
                quit_game, new_message = handle_input(key, player, world, time_manager)
                
                if quit_game:
                    game_over = True
                    message = new_message
                elif new_message == "Restarting level...":
                    world, player, time_manager = initialize_game(current_level)
                    message = new_message
                elif new_message.startswith("Enter steps back"):
                    time_travel_mode = True
                    message = new_message
                else:
                    message = new_message
        
        # Update clones at fixed intervals
        current_time = time.time()
        if current_time - last_update > TIME_STEP_DELAY:
            time_manager.update_clones(world)
            last_update = current_time
            
            # Check if level needs to be restarted when clones are done
            if message == "Restarting level...":
                world, player, time_manager = initialize_game(current_level)
                message = ""
        
        # Render the game
        render_game(stdscr, world, player, time_manager, message)
        
        # Sleep to reduce CPU usage
        time.sleep(0.01)

if __name__ == "__main__":
    # Fix path for imported modules
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    
    # Run the game with curses
    curses.wrapper(main) 