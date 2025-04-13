#!/usr/bin/env python3
"""
Temporal Maze - Automatic Demo Script

This script runs an automatic demo of the Temporal Maze game,
demonstrating key gameplay features with AI-controlled movements.
Perfect for recording demos or testing game functionality.
"""

import os
import sys
import time
import pygame
import random
import traceback

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = script_dir
sys.path.insert(0, project_root)

# Import game modules
from src.game_enhanced.constants import *
from src.game_enhanced.game import Game

class GameDemo:
    """Automated demo of the Temporal Maze game."""
    
    def __init__(self):
        """Initialize the demo."""
        self.game = Game()
        self.demo_actions = []
        self.current_action = 0
        self.action_timer = 0
        self.state = "title_screen"
        self.pause_timer = 0
        self.error_count = 0
        self.max_errors = 5
        
        # Pre-planned demo sequence
        self._setup_demo_sequence()
    
    def _setup_demo_sequence(self):
        """Set up the demo action sequence."""
        # Wait on title screen
        self.demo_actions.append({"type": "wait", "duration": 3.0})
        
        # Start the game
        self.demo_actions.append({"type": "key_press", "key": pygame.K_RETURN})
        self.demo_actions.append({"type": "wait", "duration": 2.0})
        
        # Demo basic movement with smaller steps
        self._add_movement_sequence("right", 2, 0.5)
        self._add_movement_sequence("down", 2, 0.5)
        self._add_movement_sequence("right", 2, 0.5)
        self._add_movement_sequence("up", 2, 0.5)
        
        # Wait longer to show the game state
        self.demo_actions.append({"type": "wait", "duration": 2.0})
        
        # Try time travel (press T)
        self.demo_actions.append({"type": "key_press", "key": pygame.K_t})
        self.demo_actions.append({"type": "wait", "duration": 1.0})
        
        # Select 2 steps back (press 2)
        self.demo_actions.append({"type": "key_press", "key": pygame.K_2})
        self.demo_actions.append({"type": "wait", "duration": 2.0})
        
        # Move around while clone is active - shorter movements
        self._add_movement_sequence("left", 1, 0.5)
        self._add_movement_sequence("down", 1, 0.5)
        self._add_movement_sequence("right", 2, 0.5)
        
        # Pause to show the result
        self.demo_actions.append({"type": "wait", "duration": 2.0})
        
        # Press H to show rules
        self.demo_actions.append({"type": "key_press", "key": pygame.K_h})
        self.demo_actions.append({"type": "wait", "duration": 4.0})
        
        # Press ESC to return to game
        self.demo_actions.append({"type": "key_press", "key": pygame.K_ESCAPE})
        self.demo_actions.append({"type": "wait", "duration": 1.0})
        
        # Try more movement
        self._add_movement_sequence("up", 1, 0.5)
        self._add_movement_sequence("right", 1, 0.5)
        self._add_movement_sequence("down", 1, 0.5)
        
        # Pause to show the game state
        self.demo_actions.append({"type": "wait", "duration": 1.0})
        
        # Press ESC to pause
        self.demo_actions.append({"type": "key_press", "key": pygame.K_ESCAPE})
        self.demo_actions.append({"type": "wait", "duration": 3.0})
        
        # Press ESC to resume
        self.demo_actions.append({"type": "key_press", "key": pygame.K_ESCAPE})
        self.demo_actions.append({"type": "wait", "duration": 1.0})
        
        # More movement to finish the demo
        self._add_random_movement(8, 0.5)  # Add 8 random moves
        
        # Wait at the end
        self.demo_actions.append({"type": "wait", "duration": 5.0})
    
    def _add_movement_sequence(self, direction, steps, delay=0.3):
        """Add a sequence of movement actions in the specified direction."""
        key = None
        if direction == "up":
            key = pygame.K_w
        elif direction == "down":
            key = pygame.K_s
        elif direction == "left":
            key = pygame.K_a
        elif direction == "right":
            key = pygame.K_d
        
        if key:
            for _ in range(steps):
                self.demo_actions.append({"type": "key_press", "key": key})
                self.demo_actions.append({"type": "wait", "duration": delay})
    
    def _add_random_movement(self, steps, delay=0.3):
        """Add random movement actions."""
        directions = [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]
        for _ in range(steps):
            key = random.choice(directions)
            self.demo_actions.append({"type": "key_press", "key": key})
            self.demo_actions.append({"type": "wait", "duration": delay})
    
    def run(self):
        """Run the demo."""
        try:
            # Initialize pygame
            pygame.init()
            
            # Main demo loop
            running = True
            last_time = time.time()
            
            while running:
                try:
                    # Calculate delta time
                    current_time = time.time()
                    dt = current_time - last_time
                    last_time = current_time
                    
                    # Handle real quit events
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                        elif event.type == pygame.KEYDOWN:
                            # Allow real ESC to quit the demo
                            if event.key == pygame.K_ESCAPE and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                running = False
                    
                    # Handle demo actions
                    if self.current_action < len(self.demo_actions):
                        action = self.demo_actions[self.current_action]
                        
                        if action["type"] == "wait":
                            self.action_timer += dt
                            if self.action_timer >= action["duration"]:
                                self.current_action += 1
                                self.action_timer = 0
                        
                        elif action["type"] == "key_press":
                            # Create a synthetic key press event
                            key_event = pygame.event.Event(pygame.KEYDOWN, {"key": action["key"]})
                            pygame.event.post(key_event)
                            
                            # Move to next action
                            self.current_action += 1
                    
                    # Update the game
                    self.game.handle_events()
                    self.game.update()
                    self.game.render()
                    
                    # Update the game clock and cap framerate
                    self.game.clock.tick(FPS)
                    
                    # Check if the game is still running
                    if not self.game.running:
                        running = False
                        
                except Exception as e:
                    self.error_count += 1
                    print(f"Error in demo loop: {e}")
                    traceback.print_exc()
                    
                    # Continue if we haven't hit the error limit
                    if self.error_count >= self.max_errors:
                        print(f"Too many errors ({self.error_count}), stopping demo")
                        running = False
                    else:
                        # Skip to the next action
                        self.current_action += 1
                        time.sleep(0.5)  # Pause briefly to avoid spamming errors
            
            # Clean up
            pygame.quit()
            
        except Exception as e:
            print(f"Fatal error in demo: {e}")
            traceback.print_exc()
            pygame.quit()

if __name__ == "__main__":
    demo = GameDemo()
    demo.run() 