import os
import pygame

class World:
    """
    Manages the game world, including the map, objects, and their states.
    """

    # Tile constants
    TILE_SIZE = 40
    
    # Tile types
    WALL = '#'
    FLOOR = '.'
    PLAYER_START = 'P'
    SWITCH = 'S'
    DOOR = 'D'
    EXIT = 'E'
    KEY = 'K'
    LOCKED_DOOR = 'L'
    TELEPORTER = 'T'
    
    # Time-travel specific tiles
    PAST_ONLY = 'X1'  # Only exists in the past
    PRESENT_ONLY = 'X2'  # Only exists in the present
    TIME_LOCKED = 'X3'  # Can't be time traveled from
    
    # Special markers
    ANNOTATION_A = 'A'  # Tutorial annotation point A
    ANNOTATION_B = 'B'  # Tutorial annotation point B
    ANNOTATION_C = 'C'  # Tutorial annotation point C
    
    # Colors (RGB)
    COLORS = {
        WALL: (50, 50, 50),        # Dark gray
        FLOOR: (200, 200, 200),    # Light gray
        PLAYER_START: (0, 255, 0), # Green (should not be rendered)
        SWITCH: (255, 255, 0),     # Yellow
        DOOR: (150, 75, 0),        # Brown
        EXIT: (0, 255, 0),         # Green
        KEY: (255, 215, 0),        # Gold
        LOCKED_DOOR: (139, 69, 19),# Saddle Brown
        TELEPORTER: (128, 0, 128), # Purple
        PAST_ONLY: (100, 100, 255),# Light blue
        PRESENT_ONLY: (255, 100, 100), # Light red
        TIME_LOCKED: (50, 50, 100) # Dark blue
    }
    
    def __init__(self, map_file):
        """
        Initialize the world from a map file.
        
        Args:
            map_file (str): Path to the map file
        """
        self.map_file = map_file
        self.grid = []
        self.width = 0
        self.height = 0
        self.player_start_pos = (0, 0)
        self.switches = {}  # Dict of (x, y) -> door (x, y) mapping
        self.doors = {}     # Dict of (x, y) -> is_open status
        self.keys = {}      # Dict of (x, y) -> has_been_collected
        self.locked_doors = {}  # Dict of (x, y) -> is_open status
        self.teleporters = {}   # Dict of (x, y) -> destination (x, y)
        self.annotations = {}   # Dict of (x, y) -> annotation text
        
        self.load_map(map_file)
        
        # Load tile images
        self.images = {}
        self.load_images()
        
    def load_map(self, map_file):
        """
        Load a map from a file.
        
        Args:
            map_file (str): Path to the map file
        """
        try:
            with open(map_file, 'r') as f:
                lines = f.readlines()
            
            # Process the map file
            for y, line in enumerate(lines):
                row = []
                line = line.rstrip()  # Remove trailing whitespace
                
                if len(line) == 0:
                    continue  # Skip empty lines
                
                # Update width if this row is wider
                if len(line) > self.width:
                    self.width = len(line)
                
                # Process each character in the line
                x = 0
                while x < len(line):
                    char = line[x]
                    
                    # Check for special multi-character tiles
                    if x + 1 < len(line) and char + line[x+1] in ['X1', 'X2', 'X3']:
                        tile_type = char + line[x+1]
                        row.append(tile_type)
                        x += 2
                        continue
                    
                    # Process single-character tiles
                    if char == self.PLAYER_START:
                        # Remember player's starting position
                        self.player_start_pos = (x, y)
                        # The player start is actually a floor tile
                        row.append(self.FLOOR)
                    elif char == self.SWITCH:
                        # Switches need to be paired with doors later
                        row.append(char)
                        if (x, y) not in self.switches:
                            self.switches[(x, y)] = None
                    elif char == self.DOOR:
                        # Doors start closed
                        row.append(char)
                        self.doors[(x, y)] = False
                    elif char == self.KEY:
                        # Keys start not collected
                        row.append(char)
                        self.keys[(x, y)] = False
                    elif char == self.LOCKED_DOOR:
                        # Locked doors start closed
                        row.append(char)
                        self.locked_doors[(x, y)] = False
                    elif char == self.TELEPORTER:
                        # Teleporters need to be paired later
                        row.append(char)
                        if (x, y) not in self.teleporters:
                            self.teleporters[(x, y)] = None
                    elif char in [self.ANNOTATION_A, self.ANNOTATION_B, self.ANNOTATION_C]:
                        # Store annotation location but render as floor
                        self.annotations[(x, y)] = char
                        row.append(self.FLOOR)
                    else:
                        row.append(char)
                    
                    x += 1
                
                # Ensure all rows have the same width by padding with walls
                while len(row) < self.width:
                    row.append(self.WALL)
                
                self.grid.append(row)
            
            self.height = len(self.grid)
            
            # Ensure the grid is valid
            if self.height == 0 or self.width == 0:
                raise ValueError("Map file is empty or invalid")
            
            # Pair switches with doors and teleporters (this would be more sophisticated in a real game)
            # For now, simple 1:1 mapping based on order
            doors_list = list(self.doors.keys())
            switch_positions = list(self.switches.keys())
            
            # Assign each switch to a door if there are enough doors
            for i, pos in enumerate(switch_positions):
                if i < len(doors_list):
                    self.switches[pos] = doors_list[i]
            
            # TODO: Setup teleporter pairs
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Map file not found: {map_file}")
        except Exception as e:
            raise ValueError(f"Error loading map: {e}")
    
    def load_images(self):
        """Load tile images for rendering."""
        # For now, we'll use simple colored rectangles
        # In a full implementation, you'd load actual image files
        for tile_type, color in self.COLORS.items():
            surface = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE))
            surface.fill(color)
            
            # Add some visual distinction for specific tiles
            if tile_type == self.SWITCH:
                # Draw a circle in the middle for switches
                pygame.draw.circle(surface, (255, 0, 0), 
                                  (self.TILE_SIZE // 2, self.TILE_SIZE // 2), 
                                  self.TILE_SIZE // 4)
            elif tile_type == self.DOOR:
                # Draw a darker rectangle in the middle for doors
                pygame.draw.rect(surface, (100, 50, 0), 
                                (self.TILE_SIZE // 4, self.TILE_SIZE // 4, 
                                 self.TILE_SIZE // 2, self.TILE_SIZE // 2))
            elif tile_type == self.EXIT:
                # Draw a star-like shape for exits
                pygame.draw.polygon(surface, (0, 200, 0), [
                    (self.TILE_SIZE // 2, self.TILE_SIZE // 5),
                    (self.TILE_SIZE * 3 // 5, self.TILE_SIZE * 2 // 5),
                    (self.TILE_SIZE * 4 // 5, self.TILE_SIZE * 2 // 5),
                    (self.TILE_SIZE * 3 // 5, self.TILE_SIZE * 3 // 5),
                    (self.TILE_SIZE * 7 // 10, self.TILE_SIZE * 4 // 5),
                    (self.TILE_SIZE // 2, self.TILE_SIZE * 3 // 5),
                    (self.TILE_SIZE * 3 // 10, self.TILE_SIZE * 4 // 5),
                    (self.TILE_SIZE * 2 // 5, self.TILE_SIZE * 3 // 5),
                    (self.TILE_SIZE // 5, self.TILE_SIZE * 2 // 5),
                    (self.TILE_SIZE * 2 // 5, self.TILE_SIZE * 2 // 5),
                ])
            elif tile_type == self.TELEPORTER:
                # Draw a swirl for teleporters
                for i in range(1, 4):
                    pygame.draw.circle(surface, (200, 0, 200), 
                                      (self.TILE_SIZE // 2, self.TILE_SIZE // 2), 
                                      self.TILE_SIZE // (i + 1), 1)
            
            self.images[tile_type] = surface
    
    def render(self, screen, camera_x=0, camera_y=0):
        """
        Render the world on the screen.
        
        Args:
            screen (pygame.Surface): The screen to render on
            camera_x (int): X-coordinate of the camera
            camera_y (int): Y-coordinate of the camera
        """
        # Calculate the visible range based on the screen size and tile size
        screen_width, screen_height = screen.get_size()
        visible_width = screen_width // self.TILE_SIZE + 2
        visible_height = screen_height // self.TILE_SIZE + 2
        
        # Calculate the start and end indices for rendering
        start_x = max(0, camera_x - visible_width // 2)
        end_x = min(self.width, start_x + visible_width)
        start_y = max(0, camera_y - visible_height // 2)
        end_y = min(self.height, start_y + visible_height)
        
        # Render the tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Convert grid coordinates to screen coordinates
                screen_x = (x - camera_x) * self.TILE_SIZE + screen_width // 2
                screen_y = (y - camera_y) * self.TILE_SIZE + screen_height // 2
                
                # Skip tiles that are off-screen
                if (screen_x < -self.TILE_SIZE or screen_x > screen_width or
                    screen_y < -self.TILE_SIZE or screen_y > screen_height):
                    continue
                
                # Get the tile type
                tile_type = self.grid[y][x]
                
                # Handle doors that might be open
                if (x, y) in self.doors and self.doors[(x, y)]:
                    tile_type = self.FLOOR  # Open door becomes floor
                
                # Handle locked doors that might be open
                if (x, y) in self.locked_doors and self.locked_doors[(x, y)]:
                    tile_type = self.FLOOR  # Open locked door becomes floor
                
                # Handle keys that might be collected
                if (x, y) in self.keys and self.keys[(x, y)]:
                    tile_type = self.FLOOR  # Collected key becomes floor
                
                # Get the tile image
                if tile_type in self.images:
                    image = self.images[tile_type]
                    screen.blit(image, (screen_x, screen_y))
                else:
                    # For complex tiles like X1, X2, etc., use default colors
                    if tile_type.startswith('X'):
                        color = self.COLORS.get(tile_type, (150, 150, 150))
                        pygame.draw.rect(screen, color, 
                                        (screen_x, screen_y, self.TILE_SIZE, self.TILE_SIZE))
                    else:
                        # Default to floor for unknown tiles
                        screen.blit(self.images[self.FLOOR], (screen_x, screen_y))
    
    def get_tile(self, x, y):
        """
        Get the tile type at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            str: The tile type, or None if out of bounds
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None
    
    def can_move_to(self, x, y):
        """
        Check if a position is valid for movement.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            bool: True if the position is valid for movement, False otherwise
        """
        # Check if the position is within bounds
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        
        # Get the tile type
        tile_type = self.grid[y][x]
        
        # Check if the tile is a wall
        if tile_type == self.WALL:
            return False
        
        # Check if the tile is a closed door
        if (x, y) in self.doors and not self.doors[(x, y)]:
            return False
        
        # Check if the tile is a closed locked door
        if (x, y) in self.locked_doors and not self.locked_doors[(x, y)]:
            return False
        
        # All other tiles are valid for movement
        return True
    
    def press_switch(self, x, y):
        """
        Press a switch at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            bool: True if a switch was pressed, False otherwise
        """
        if (x, y) in self.switches:
            door_pos = self.switches[(x, y)]
            if door_pos and door_pos in self.doors:
                self.doors[door_pos] = True
                return True
        return False
    
    def release_switch(self, x, y):
        """
        Release a switch at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            bool: True if a switch was released, False otherwise
        """
        if (x, y) in self.switches:
            door_pos = self.switches[(x, y)]
            if door_pos and door_pos in self.doors:
                self.doors[door_pos] = False
                return True
        return False
    
    def collect_key(self, x, y):
        """
        Collect a key at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            bool: True if a key was collected, False otherwise
        """
        if (x, y) in self.keys and not self.keys[(x, y)]:
            self.keys[(x, y)] = True
            return True
        return False
    
    def unlock_door(self, x, y):
        """
        Unlock a door at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            bool: True if a door was unlocked, False otherwise
        """
        if (x, y) in self.locked_doors and not self.locked_doors[(x, y)]:
            # Check if all keys have been collected
            all_keys_collected = all(self.keys.values())
            if all_keys_collected:
                self.locked_doors[(x, y)] = True
                return True
        return False
    
    def is_exit(self, x, y):
        """
        Check if a position is an exit.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            bool: True if the position is an exit, False otherwise
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x] == self.EXIT
        return False
    
    def teleport(self, x, y):
        """
        Get the destination of a teleporter at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            tuple: The destination (x, y), or None if not a teleporter
        """
        if (x, y) in self.teleporters:
            return self.teleporters[(x, y)]
        return None
    
    def get_annotation(self, x, y):
        """
        Get the annotation at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            str: The annotation identifier, or None if no annotation
        """
        return self.annotations.get((x, y), None)
    
    def get_player_start_pos(self):
        """
        Get the player's starting position.
        
        Returns:
            tuple: The player's starting position (x, y)
        """
        return self.player_start_pos 