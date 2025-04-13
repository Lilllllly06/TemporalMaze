"""
Entity classes for Temporal Maze.
Handles player, clones, guards, and items.
"""

import math
import random
from .constants import *
import traceback

class Entity:
    """Base entity class."""
    
    def __init__(self, x, y):
        """
        Initialize an entity at a specific position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        self.x = x
        self.y = y
        self.visible = True
    
    def get_position(self):
        """
        Get the entity's position.
        
        Returns:
            tuple: (x, y) position
        """
        return (self.x, self.y)
    
    def set_position(self, x, y):
        """
        Set the entity's position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        self.x = x
        self.y = y
    
    def update(self, game_state):
        """
        Update the entity's state.
        To be overridden by subclasses.
        
        Args:
            game_state: The game state
        """
        pass
    
    def render(self, surface, camera_offset=(0, 0)):
        """
        Render the entity.
        To be overridden by subclasses.
        
        Args:
            surface: Pygame surface to render on
            camera_offset (tuple): Camera offset (x, y)
        """
        pass

class Player(Entity):
    """Player entity that can move around and interact with the world."""
    
    def __init__(self, x, y):
        """
        Initialize the player.
        
        Args:
            x (int): Initial X coordinate
            y (int): Initial Y coordinate
        """
        super().__init__(x, y)
        self.keys = 0
        self.energy = PLAYER_START_ENERGY # Use constant
        self.energy_max = PLAYER_START_ENERGY # Max energy
        self.paw_prints = []
        self.facing = "right" 
        self.world = None
        self.direction = (0, 0) 
        self.inventory = [] 
        self.history = [] # Initialize history list
        self.history_limit = MAX_HISTORY 
    
    def move(self, dx, dy, world):
        """
        Attempt to move the player by the given delta.
        
        Args:
            dx (int): X-axis movement
            dy (int): Y-axis movement
            world: The game world
            
        Returns:
            bool: True if the move was successful
        """
        # Store reference to world
        self.world = world
        
        # Record position BEFORE trying to move
        self.record_position()
        
        # Update player direction
        if dx != 0 or dy != 0:
            self.direction = (dx, dy)
            # Update visual facing direction
            if dx > 0: self.facing = "right"
            elif dx < 0: self.facing = "left"
            elif dy > 0: self.facing = "down"
            elif dy < 0: self.facing = "up"
            # Add paw print
            self.paw_prints.append({"x": self.x, "y": self.y, "frame": 0, "time": 1.0})
        
        # Calculate new position
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Get tile at new position
        tile = world.get_tile_at(new_x, new_y)
        
        # --- Check 1: Basic Walkable Tiles --- 
        if world.is_walkable(new_x, new_y):
            # Handle interactions ON the tile being moved TO
            if tile == TILE_SWITCH:
                 # If stepping ONTO a switch, activate it
                 world.activate_switch(new_x, new_y)
            elif tile == TILE_EXIT:
                world.level_completed = True 
                return False # Prevent moving onto exit, just trigger win
            elif tile == TILE_PORTAL_A or tile == TILE_PORTAL_B:
                portal_pos = world.get_paired_portal((new_x, new_y))
                if portal_pos:
                    # Stepping OFF a switch before teleport?
                    if world.get_tile_at(self.x, self.y) == TILE_SWITCH:
                         world.deactivate_switch(self.x, self.y)
                    self.x, self.y = portal_pos
                    self.record_position() # Record arrival position
                    return True 
            elif tile == TILE_ITEM_KEY:
                self.keys += 1
                world.remove_item(new_x, new_y)
                # Update inventory if needed
            elif tile == TILE_ITEM_POTION:
                self.energy = min(self.energy_max, self.energy + 1)
                world.remove_item(new_x, new_y)
                # Update inventory if needed
            # Terminal interaction is handled by 'E' key now
            
            # Stepping OFF a switch?
            if world.get_tile_at(self.x, self.y) == TILE_SWITCH:
                 world.deactivate_switch(self.x, self.y)
                 
            # Complete the move
            self.x = new_x
            self.y = new_y
            return True
            
        # --- Check 2: Locked Door Interaction --- 
        # Check if the target tile is a door (could be open or closed)
        # Use get_tile_at for safety, even though is_walkable failed
        target_tile_type = world.get_tile_at(new_x, new_y)
        if target_tile_type == TILE_DOOR_CLOSED:
             # Check if this specific door requires a key (using its position)
             # We need a way to know which doors are key-locked vs switch-locked.
             # For now, assume door at tutorial position (8, 1) is the key door.
             # A better approach would be to store door type in world.doors
             is_key_door = (new_x, new_y) == (8, 1) # Updated from (10, 1) to match new level1.txt
             
             if is_key_door and self.keys > 0:
                  print("Opening locked door with key!")
                  self.keys -= 1
                  world.open_door(new_x, new_y) # This sets door state and tile type
                  # Stepping off switch?
                  if world.get_tile_at(self.x, self.y) == TILE_SWITCH:
                       world.deactivate_switch(self.x, self.y)
                  # Complete the move onto the (now open) door tile
                  self.x = new_x
                  self.y = new_y
                  return True
             else:
                  # It's a closed door we can't open (no key or switch door)
                  print(f"Move blocked by closed door at ({new_x}, {new_y}). Key needed: {is_key_door}, Keys held: {self.keys}")
                  return False

        # --- Move Failed --- 
        # If not walkable and not an openable locked door
        print(f"Move to ({new_x}, {new_y}) failed. Tile: {target_tile_type}")
        return False
    
    def record_position(self):
        """Record the current position and direction in history."""
        # Don't record if the position hasn't changed (prevents duplicate entries)
        if not self.history or (self.x, self.y) != (self.history[-1]['x'], self.history[-1]['y']):
             current_state = {
                 'x': self.x,
                 'y': self.y,
                 'direction': self.facing # Record visual facing direction
             }
             self.history.append(current_state)
             
             # Keep history within limit
             if len(self.history) > self.history_limit:
                 self.history.pop(0)
    
    def get_history(self, steps_back=None):
        """
        Get movement history.
        
        Args:
            steps_back (int, optional): Number of steps to get from history
                                       
        Returns:
            list: List of (x, y, direction) tuples
        """
        if steps_back is None or steps_back >= len(self.history):
            return self.history.copy()
        else:
            return self.history[-steps_back:]
    
    def reset_history(self):
        """Clear the movement history."""
        self.history = []
    
    def create_clone(self, steps_back):
        """
        Create a new time clone.
        
        Args:
            steps_back (int): How many steps to go back in time
            
        Returns:
            TimeClone: The created clone or None if creation failed
        """
        if self.energy <= 0:
            return None
            
        history = self.get_history(steps_back)
        if not history:
            return None
            
        self.energy -= 1
        return TimeClone(history[0][0], history[0][1], history)
    
    def update(self, game_state):
        """Update the player."""
        # Update paw prints
        for i, paw in enumerate(self.paw_prints):
            paw["time"] -= game_state.dt
            if paw["time"] <= 0:
                paw["frame"] += 1
                paw["time"] = 0.2  # Frame duration
                if paw["frame"] >= 4:  # Remove after all frames
                    self.paw_prints[i] = None
        
        # Remove expired paw prints
        self.paw_prints = [paw for paw in self.paw_prints if paw is not None]
        
        # Check for collisions with guards
        for guard in game_state.guards:
            if (self.x == guard.x and self.y == guard.y) and guard.state != GUARD_CHASING:
                # Alert the guard
                guard.alert(self.get_position())

    def time_travel(self, steps, game_state):
        """Creates a time clone based on past history."""
        print(f"[TIME TRAVEL START] Trying {steps} steps back. History len: {len(self.history)}. Energy: {self.energy}")
        
        if self.energy <= 0:
            print("[TIME TRAVEL FAIL] No energy.")
            game_state.show_message("Not enough energy!", 2)
            return False
            
        # Ensure steps are valid (need at least 1 step for a clone, and history must be long enough)
        if steps < 1 or steps >= len(self.history):
            max_steps = len(self.history) - 1
            print(f"[TIME TRAVEL FAIL] Invalid steps ({steps}). Need 1-{max_steps}. History len: {len(self.history)}")
            game_state.show_message(f"Invalid steps (need 1-{max_steps})", 2)
            return False
            
        # History slice: from beginning up to 'steps' ago
        history_slice = self.history[:-steps]
        print(f"[TIME TRAVEL] History slice length: {len(history_slice)}")
        
        if not history_slice:
             print("[TIME TRAVEL FAIL] History slice is empty.")
             game_state.show_message("Not enough history recorded for this travel!", 2)
             return False
             
        start_state = history_slice[0] 
        clone_history = history_slice 

        print(f"[TIME TRAVEL] Creating clone at {start_state['x']},{start_state['y']} with {len(clone_history)} history steps.")

        # Create the clone
        try:
             new_clone = TimeClone(start_state['x'], start_state['y'], clone_history)
             print("[TIME TRAVEL] Clone instance created.")
        except Exception as e:
             print(f"[TIME TRAVEL FAIL] Error creating TimeClone instance: {e}")
             traceback.print_exc()
             game_state.show_message("Error initializing clone.", 2)
             return False
        
        # Add clone to the game state's list
        if hasattr(game_state, 'clones') and isinstance(game_state.clones, list):
            game_state.clones.append(new_clone)
            self.energy -= 1 # Consume energy
            print(f"[TIME TRAVEL SUCCESS] Clone added. Energy left: {self.energy}. Total clones: {len(game_state.clones)}")
            return True
        else:
            print("[TIME TRAVEL FAIL] Game state missing 'clones' list or it's not a list.")
            game_state.show_message("Error adding clone to game.", 2)
            return False
            
    def interact(self, game_state):
        """Interact with adjacent tiles (terminals, switches)."""
        for dx, dy in [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)]: # Check current and adjacent
            check_x, check_y = self.x + dx, self.y + dy
            tile_type = game_state.world.get_tile_at(check_x, check_y)
            
            if tile_type == TILE_TERMINAL:
                message = game_state.world.activate_terminal(check_x, check_y)
                if message:
                    game_state.show_message(message, 5.0)
                    # Potentially change game state to STATE_DIALOGUE if needed
                return # Interact with first found
            elif tile_type == TILE_SWITCH:
                 # Check if switch is already active
                if (check_x, check_y) in game_state.world.activated_switches:
                     game_state.world.deactivate_switch(check_x, check_y)
                     game_state.show_message("Switch deactivated.", 1.0)
                else:
                     game_state.world.activate_switch(check_x, check_y)
                     game_state.show_message("Switch activated!", 1.0)
                return # Interact with first found

class TimeClone(Entity):
    """Time clone entity that replays the player's movements."""
    
    def __init__(self, x, y, history):
        """
        Initialize a time clone.
        
        Args:
            x (int): Initial X coordinate
            y (int): Initial Y coordinate
            history (list): List of (x, y, direction) tuples to replay
        """
        super().__init__(x, y)
        self.history = history.copy()
        self.current_step = 0
        self.direction = history[0]['direction'] if history else 'right' # Default if history is empty
        self.facing = self.direction # Initial facing matches direction
        self.active = True
        self.paw_prints = [] 
    
    def update(self, game_state):
        """
        Update the clone's position based on history.
        
        Args:
            game_state: The game state
        """
        if not self.active or self.current_step >= len(self.history):
            self.active = False
            return False
        
        # Get the next state dictionary from history
        next_state = self.history[self.current_step]
        next_x = next_state['x']
        next_y = next_state['y']
        next_facing = next_state['direction'] # Use the recorded facing direction
        
        # Update direction and facing based on the recorded state
        self.facing = next_facing
        # (Optional: you could calculate dx/dy if needed, but facing is more direct)
        
        # Add paw print at current position before moving
        if self.x != next_x or self.y != next_y:
            self.paw_prints.append({"x": self.x, "y": self.y, "frame": 0, "time": 1.0})
        
        # Check if we're stepping off a switch
        world = game_state.world
        if world.get_tile_at(self.x, self.y) == TILE_SWITCH:
            world.deactivate_switch(self.x, self.y)
        
        # Update position
        self.x = next_x
        self.y = next_y
        
        # Check if we stepped on a switch
        if world.get_tile_at(self.x, self.y) == TILE_SWITCH:
            world.activate_switch(self.x, self.y)
        
        # Increment step counter
        self.current_step += 1
        
        # Check if we've reached the end of the history
        if self.current_step >= len(self.history):
            self.active = False
            # If clone finishes on a switch, ensure it stays deactivated
            if world.get_tile_at(self.x, self.y) == TILE_SWITCH:
                world.deactivate_switch(self.x, self.y)
            
        return self.active

class Guard(Entity):
    """Guard entity that patrols and can chase the player."""
    
    def __init__(self, x, y, patrol_route=None):
        """
        Initialize a guard entity.
        
        Args:
            x (int): Initial X coordinate
            y (int): Initial Y coordinate
            patrol_route (list, optional): List of (x, y) positions to patrol
        """
        super().__init__(x, y)
        self.state = GUARD_PATROLLING
        self.direction = DOWN
        self.speed = 1
        self.view_distance = 5
        self.alert_timer = 0
        self.alert_duration = 3  # seconds
        self.target_position = None
        
        # Set up patrol route
        if patrol_route:
            self.patrol_route = patrol_route
        else:
            # Default patrol is 4 steps in each cardinal direction
            self.patrol_route = [
                (x, y), 
                (x + 4, y),
                (x + 4, y + 4),
                (x, y + 4)
            ]
        self.patrol_index = 0
        self.patrol_timer = 0
        self.patrol_wait = 1.5  # seconds to wait at each patrol point
    
    def update(self, game_state):
        """
        Update the guard's state and position.
        
        Args:
            game_state: The game state
        """
        dt = game_state.dt
        world = game_state.world
        
        if self.state == GUARD_PATROLLING:
            # Wait at patrol points
            if self.patrol_timer > 0:
                self.patrol_timer -= dt
                return
                
            # Move along patrol route
            target_x, target_y = self.patrol_route[self.patrol_index]
            
            # If we've reached the target, move to the next patrol point
            if self.x == target_x and self.y == target_y:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_route)
                self.patrol_timer = self.patrol_wait
                return
                
            # Move toward the target
            self._move_toward(target_x, target_y, world)
            
            # Check for player in line of sight
            if self._can_see_player(game_state.player, world):
                self.alert(game_state.player.get_position())
                
        elif self.state == GUARD_ALERTED:
            # Count down alert timer
            self.alert_timer -= dt
            
            if self.alert_timer <= 0:
                # Change to chasing state if player is still visible
                if self._can_see_player(game_state.player, world):
                    self.state = GUARD_CHASING
                    self.target_position = game_state.player.get_position()
                else:
                    # Return to patrolling
                    self.state = GUARD_PATROLLING
                    
        elif self.state == GUARD_CHASING:
            # Chase the player
            if self.target_position:
                target_x, target_y = self.target_position
                
                # Move toward the target
                self._move_toward(target_x, target_y, world)
                
                # Update target if the player is visible
                if self._can_see_player(game_state.player, world):
                    self.target_position = game_state.player.get_position()
                # If we've reached the last known position and can't see the player, return to patrol
                elif self.x == target_x and self.y == target_y:
                    self.state = GUARD_PATROLLING
                    
            else:
                # If no target, return to patrolling
                self.state = GUARD_PATROLLING
                
            # Check for player collision
            if (self.x == game_state.player.x and self.y == game_state.player.y):
                # Player is caught!
                game_state.player_caught = True
    
    def alert(self, player_pos):
        """
        Alert the guard to the player's presence.
        
        Args:
            player_pos (tuple): Player's position (x, y)
        """
        self.state = GUARD_ALERTED
        self.alert_timer = self.alert_duration
        self.target_position = player_pos
    
    def _move_toward(self, target_x, target_y, world):
        """
        Move toward a target position.
        
        Args:
            target_x (int): Target X coordinate
            target_y (int): Target Y coordinate
            world: The game world
        """
        # Calculate direction to target
        dx = 0
        dy = 0
        
        if self.x < target_x:
            dx = 1
        elif self.x > target_x:
            dx = -1
            
        if self.y < target_y:
            dy = 1
        elif self.y > target_y:
            dy = -1
        
        # Prioritize the largest distance
        if abs(target_x - self.x) > abs(target_y - self.y):
            # Try horizontal first
            if self._try_move(dx, 0, world):
                return
            elif self._try_move(0, dy, world):
                return
        else:
            # Try vertical first
            if self._try_move(0, dy, world):
                return
            elif self._try_move(dx, 0, world):
                return
                
        # Try diagonal if direct approaches fail
        self._try_move(dx, dy, world)
    
    def _try_move(self, dx, dy, world):
        """
        Try to move in a direction.
        
        Args:
            dx (int): X-axis movement
            dy (int): Y-axis movement
            world: The game world
            
        Returns:
            bool: True if the move was successful
        """
        if dx != 0 or dy != 0:
            self.direction = (dx, dy)
            
        new_x = self.x + dx
        new_y = self.y + dy
        
        if world.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
            return True
            
        return False
    
    def _can_see_player(self, player, world):
        """
        Check if the guard can see the player.
        
        Args:
            player: The player entity
            world: The game world
            
        Returns:
            bool: True if the player is visible
        """
        # Get player position
        player_x, player_y = player.get_position()
        
        # Calculate distance to player
        distance = math.sqrt((player_x - self.x)**2 + (player_y - self.y)**2)
        
        # Check if player is within view distance
        if distance > self.view_distance:
            return False
        
        # Check if there are walls blocking the view
        if self.x == player_x:
            # Vertical line of sight
            start_y = min(self.y, player_y)
            end_y = max(self.y, player_y)
            for y in range(start_y, end_y + 1):
                if not world.is_transparent(self.x, y):
                    return False
            return True
            
        elif self.y == player_y:
            # Horizontal line of sight
            start_x = min(self.x, player_x)
            end_x = max(self.x, player_x)
            for x in range(start_x, end_x + 1):
                if not world.is_transparent(x, self.y):
                    return False
            return True
            
        else:
            # Not in direct line of sight
            return False

class Item(Entity):
    """Item entity class."""
    
    def __init__(self, x, y, item_type):
        """
        Initialize an item entity.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            item_type (int): Type of item (TILE_ITEM_KEY, TILE_ITEM_POTION, etc.)
        """
        super().__init__(x, y)
        self.item_type = item_type
        
        # Set up item properties
        if item_type == TILE_ITEM_KEY:
            self.name = "Key"
            self.description = "Opens a locked door"
        elif item_type == TILE_ITEM_POTION:
            self.name = "Time Energy"
            self.description = "Restores time travel energy"
        else:
            self.name = "Unknown Item"
            self.description = "???"

class Terminal(Entity):
    """Terminal entity for story elements and hints."""
    
    def __init__(self, x, y, message):
        """
        Initialize a terminal entity.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            message (str): Message to display when activated
        """
        super().__init__(x, y)
        self.message = message
        self.activated = False
    
    def activate(self):
        """Activate the terminal."""
        self.activated = True
        return self.message 