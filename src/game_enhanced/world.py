"""
World module for the enhanced Temporal Maze game.
"""

import random
import numpy as np
from .constants import *
from .assets import assets

class World:
    """Manages the game world, including the map, objects, and their states."""
    
    def __init__(self, width_or_data=None, height=None):
        """
        Initialize the world.
        
        Args:
            width_or_data: Either the width of the world or level_data
            height: Height of the world (optional if width_or_data is level_data)
        """
        # Initialize variables
        self.width = 0
        self.height = 0
        self.map = None
        self.player_start = (1, 1)
        self.switches = {}  # (x, y) -> List of door_positions it controls
        self.doors = {}     # (x, y) -> {"required_switches": set(), "is_open": bool}
        self.portals = {}   # (x, y) -> (x2, y2) (paired portal)
        self.items = {}     # (x, y) -> item_type
        self.terminals = {} # (x, y) -> message
        self.activated_switches = set() # Set of (x, y) tuples for active switches
        self.exit_pos = None
        self.level_completed = False
        
        # Story elements and dialogue
        self.story_messages = [
            "Welcome to the Temporal Research Facility. Our experiments with time have created... anomalies.",
            "Be careful with the temporal energy. Each clone you create depletes your reserves.",
            "The guards are programmed to detect unauthorized personnel. Avoid their line of sight.",
            "The facility's emergency exits are locked. You'll need to find switches to open them.",
            "Our portal technology is unstable but functional. Use the paired portals to move quickly.",
            "Time and space are connected here. What you do in one moment affects all others.",
            "Some doors require special keys. Look for them throughout the facility.",
            "The deeper you go, the more unstable the time field becomes. Prepare for anomalies.",
            "If you see yourself from another timeline, don't be alarmed. Time clones are harmless.",
            "Find the central control room to shut down the facility and escape this time loop."
        ]
        
        # Initialize based on parameters
        if width_or_data is not None:
            if height is not None:
                # Initialize with width and height
                self.width = width_or_data
                self.height = height
                self.map = np.full((self.height, self.width), TILE_FLOOR, dtype=int)
            else:
                # Initialize with level data
                self.load_from_data(width_or_data)
    
    def load_from_data(self, level_data):
        """
        Load a level from data tuple or dictionary.
        
        Args:
            level_data: Level data in dictionary format or tuple format
        """
        try:
            # Handle dictionary format (from the level generator)
            if isinstance(level_data, dict):
                self._load_from_dict(level_data)
                return
                
            # Handle the original tuple format
            level_map, player_start, switch_positions, door_positions, portals_data, guard_positions, items_data, terminal_pos = level_data
            
            # Set basic properties
            self.map = level_map
            self.height, self.width = level_map.shape
            self.player_start = player_start
            
            # Process switches and doors
            for i, switch_pos in enumerate(switch_positions):
                self.switches[switch_pos] = []
                
            for i, door_pos in enumerate(door_positions):
                self.doors[door_pos] = {"required_switches": set(), "is_open": False}
                
                # Associate with switches (each switch opens all doors in this simple implementation)
                for switch_pos in switch_positions:
                    self.switches[switch_pos].append(door_pos)
            
            # Process portals
            for portal_a, portal_b in portals_data:
                self.portals[portal_a] = portal_b
                self.portals[portal_b] = portal_a
            
            # Process items
            for item_pos, item_type in items_data:
                self.items[item_pos] = item_type
            
            # Process terminal with random story message
            if terminal_pos:
                self.terminals[terminal_pos] = random.choice(self.story_messages)
            
            # Find exit
            for y in range(self.height):
                for x in range(self.width):
                    if self.map[y][x] == TILE_EXIT:
                        self.exit_pos = (x, y)
                        break
        except Exception as e:
            print(f"Error loading level data: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_from_dict(self, level_data):
        """Load level from dictionary format (produced by level generator)."""
        # Set dimensions
        self.width = level_data.get("width", 20)
        self.height = level_data.get("height", 15)
        
        # Create map
        self.map = np.full((self.height, self.width), TILE_FLOOR, dtype=int)
        
        # Set walls and other tiles
        for y in range(self.height):
            for x in range(self.width):
                tile_val = level_data.get("map", {}).get((x, y), TILE_FLOOR)
                self.map[y][x] = tile_val
        
        # Set player start
        self.player_start = level_data.get("player_start", (1, 1))
        
        # Process switches and doors
        self.switches = level_data.get("switches", {})
        self.doors = level_data.get("doors", {})
        
        # Process portals
        self.portals = level_data.get("portals", {})
        
        # Process items
        self.items = level_data.get("items", {})
        
        # Process terminals
        self.terminals = level_data.get("terminals", {})
        
        # Find exit
        self.exit_pos = level_data.get("exit_pos", None)
        
        # If exit not provided, try to find it
        if not self.exit_pos:
            for y in range(self.height):
                for x in range(self.width):
                    if self.map[y][x] == TILE_EXIT:
                        self.exit_pos = (x, y)
                        break
    
    def get_tile(self, x, y):
        """Wrapper for get_tile_at for compatibility."""
        return self.get_tile_at(x, y)
        
    def set_tile(self, x, y, tile_type):
        """Set a tile at the specified position."""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.map[y][x] = tile_type
            
            # Special case for exit
            if tile_type == TILE_EXIT:
                self.exit_pos = (x, y)
    
    def get_tile_at(self, x, y):
        """
        Get the tile at the specified position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            int: Tile type at the position or TILE_WALL if out of bounds
        """
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.map[y][x]
        return TILE_WALL  # Outside the map is considered a wall
    
    def _update_doors(self):
        """Update the state of all doors based on currently active switches."""
        for door_pos, door_data in self.doors.items():
            required = door_data["required_switches"]
            is_open = required.issubset(self.activated_switches)
            
            if door_data["is_open"] != is_open:
                door_data["is_open"] = is_open
                door_x, door_y = door_pos
                if 0 <= door_y < self.height and 0 <= door_x < self.width:
                    self.map[door_y][door_x] = TILE_DOOR_OPEN if is_open else TILE_DOOR_CLOSED
    
    def activate_switch(self, x, y):
        """
        Activate a switch at the specified position and update doors.
        Args: x (int), y (int)
        """
        switch_pos = (x, y)
        if switch_pos in self.switches and switch_pos not in self.activated_switches:
            self.activated_switches.add(switch_pos)
            self._update_doors()
            
    def deactivate_switch(self, x, y):
        """
        Deactivate a switch at the specified position and update doors.
        Args: x (int), y (int)
        """
        switch_pos = (x, y)
        if switch_pos in self.activated_switches:
            self.activated_switches.remove(switch_pos)
            self._update_doors()
    
    def open_door(self, x, y):
        """
        Open a door with a key.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        door_pos = (x, y)
        if door_pos in self.doors:
            self.doors[door_pos]["is_open"] = True
            if 0 <= y < self.height and 0 <= x < self.width:
                self.map[y][x] = TILE_DOOR_OPEN
    
    def get_paired_portal(self, portal_pos):
        """
        Get the paired portal position.
        
        Args:
            portal_pos (tuple): Portal position (x, y)
            
        Returns:
            tuple: Paired portal position (x, y) or None if not found
        """
        return self.portals.get(portal_pos)
    
    def remove_item(self, x, y):
        """
        Remove an item from the map.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        item_pos = (x, y)
        if item_pos in self.items:
            del self.items[item_pos]
            
        # Update the map
        if 0 <= y < self.height and 0 <= x < self.width:
            self.map[y][x] = TILE_FLOOR
    
    def activate_terminal(self, x, y):
        """
        Activate a terminal to display a message.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            str: Terminal message or None if not a terminal
        """
        terminal_pos = (x, y)
        return self.terminals.get(terminal_pos)
    
    def render(self, surface, camera_offset=(0, 0)):
        """
        Render the world on the screen.
        
        Args:
            surface: Pygame surface to render on
            camera_offset (tuple): Camera offset (x, y)
        """
        cam_x, cam_y = camera_offset
        
        # Calculate visible range
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Determine the range of tiles to render
        start_x = max(0, cam_x // TILE_SIZE)
        end_x = min(self.width, (cam_x + screen_width) // TILE_SIZE + 1)
        start_y = max(0, cam_y // TILE_SIZE)
        end_y = min(self.height, (cam_y + screen_height) // TILE_SIZE + 1)
        
        # Render each tile
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Get the tile type
                tile_type = self.map[y][x]
                
                # Get the corresponding image
                image = None
                
                if tile_type == TILE_WALL:
                    image = assets.get_image("wall")
                elif tile_type == TILE_FLOOR:
                    image = assets.get_image("floor")
                elif tile_type == TILE_SWITCH:
                    image = assets.get_image("switch")
                elif tile_type == TILE_DOOR_CLOSED:
                    image = assets.get_image("door_closed")
                elif tile_type == TILE_DOOR_OPEN:
                    image = assets.get_image("door_open")
                elif tile_type == TILE_EXIT:
                    image = assets.get_image("exit")
                elif tile_type == TILE_PORTAL_A:
                    image = assets.get_image("portal_a")
                elif tile_type == TILE_PORTAL_B:
                    image = assets.get_image("portal_b")
                elif tile_type == TILE_ITEM_KEY:
                    image = assets.get_image("key")
                elif tile_type == TILE_ITEM_POTION:
                    image = assets.get_image("potion")
                elif tile_type == TILE_TERMINAL:
                    image = assets.get_image("terminal")
                
                # Draw the tile
                if image:
                    draw_x = x * TILE_SIZE - cam_x
                    draw_y = y * TILE_SIZE - cam_y
                    surface.blit(image, (draw_x, draw_y))
    
    def is_level_completed(self):
        """
        Check if the level is completed.
        
        Returns:
            bool: True if the level is completed
        """
        return self.level_completed 

    def is_walkable(self, x, y):
        """
        Check if a tile is walkable.
        """
        tile = self.get_tile_at(x, y)
        
        # Basic walkable tiles
        if tile in [TILE_FLOOR, TILE_SWITCH, TILE_EXIT, TILE_PORTAL_A, TILE_PORTAL_B, 
                    TILE_ITEM_KEY, TILE_ITEM_POTION, TILE_TERMINAL]:
            return True
            
        # Special case for doors - check internal state
        if tile == TILE_DOOR_CLOSED or tile == TILE_DOOR_OPEN:
            door_data = self.doors.get((x,y))
            return door_data["is_open"] if door_data else False # Walkable only if door exists and is open
            
        return False

    def is_transparent(self, x, y):
        """
        Check if a tile is transparent (allows line of sight).
        """
        tile = self.get_tile_at(x, y)
        # Open doors are transparent
        if tile == TILE_DOOR_OPEN:
            return True
        # Walls and closed doors are not
        return tile != TILE_WALL and tile != TILE_DOOR_CLOSED 