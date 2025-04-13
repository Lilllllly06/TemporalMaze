import pygame

class Player:
    """Handles player movement and interaction with the game world."""
    
    # Constants
    MAX_HISTORY = 50  # Maximum number of steps to remember for time travel
    
    def __init__(self, x, y):
        """
        Initialize a player at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
        """
        self.x = x
        self.y = y
        self.history = []  # List of past positions [(x, y), ...]
        self.collected_keys = 0
        self.can_time_travel = True
        
        # Initialize sprites
        self.sprite = None
        self.load_sprites()
    
    def load_sprites(self):
        """Load player sprites."""
        # Create a simple colored square for the player
        self.sprite = pygame.Surface((30, 30))
        self.sprite.fill((0, 0, 255))  # Blue player
        
        # Draw eyes to indicate direction facing
        pygame.draw.circle(self.sprite, (255, 255, 255), (10, 10), 5)
        pygame.draw.circle(self.sprite, (255, 255, 255), (20, 10), 5)
        pygame.draw.circle(self.sprite, (0, 0, 0), (10, 10), 2)
        pygame.draw.circle(self.sprite, (0, 0, 0), (20, 10), 2)
    
    def move(self, dx, dy, world):
        """
        Move the player by the specified delta, checking for collisions.
        
        Args:
            dx (int): Change in x-coordinate
            dy (int): Change in y-coordinate
            world (World): The game world
            
        Returns:
            bool: True if the player moved, False otherwise
        """
        # Record current position in history
        self.add_to_history(self.x, self.y)
        
        # Check if the new position is valid
        new_x = self.x + dx
        new_y = self.y + dy
        
        if world.can_move_to(new_x, new_y):
            # Check for special tiles at the new position
            tile = world.get_tile(new_x, new_y)
            
            # Handle switch tiles
            if tile == world.SWITCH:
                world.press_switch(new_x, new_y)
            
            # Handle key tiles
            if tile == world.KEY:
                if world.collect_key(new_x, new_y):
                    self.collected_keys += 1
            
            # Handle locked door tiles
            if tile == world.LOCKED_DOOR:
                # Try to unlock the door
                if not world.unlock_door(new_x, new_y):
                    # Failed to unlock, can't move
                    return False
            
            # Handle teleporter tiles
            if tile == world.TELEPORTER:
                dest = world.teleport(new_x, new_y)
                if dest:
                    # Teleport to the destination
                    new_x, new_y = dest
            
            # Move the player
            self.x = new_x
            self.y = new_y
            return True
        
        return False
    
    def add_to_history(self, x, y):
        """
        Add a position to the player's history.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
        """
        self.history.append((x, y))
        
        # Trim history if it gets too long
        if len(self.history) > self.MAX_HISTORY:
            self.history.pop(0)
    
    def get_history(self, steps_back=None):
        """
        Get the player's history.
        
        Args:
            steps_back (int): Number of steps to go back, or None for all history
            
        Returns:
            list: List of positions [(x, y), ...]
        """
        if steps_back is None or steps_back >= len(self.history):
            return self.history.copy()
        else:
            return self.history[-steps_back:]
    
    def get_position(self):
        """
        Get the player's current position.
        
        Returns:
            tuple: Current position (x, y)
        """
        return (self.x, self.y)
    
    def set_position(self, x, y):
        """
        Set the player's position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
        """
        self.x = x
        self.y = y
    
    def render(self, screen, camera_x=0, camera_y=0):
        """
        Render the player on the screen.
        
        Args:
            screen (pygame.Surface): The screen to render on
            camera_x (int): X-coordinate of the camera
            camera_y (int): Y-coordinate of the camera
        """
        # Calculate screen position
        tile_size = 40  # This should match World.TILE_SIZE
        screen_width, screen_height = screen.get_size()
        
        screen_x = (self.x - camera_x) * tile_size + screen_width // 2
        screen_y = (self.y - camera_y) * tile_size + screen_height // 2
        
        # Center the sprite in the tile
        offset_x = (tile_size - self.sprite.get_width()) // 2
        offset_y = (tile_size - self.sprite.get_height()) // 2
        
        # Render the player
        screen.blit(self.sprite, (screen_x + offset_x, screen_y + offset_y))
    
    def is_at_position(self, x, y):
        """
        Check if the player is at the specified position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            bool: True if the player is at the position, False otherwise
        """
        return self.x == x and self.y == y
    
    def disable_time_travel(self):
        """Disable time travel for the player."""
        self.can_time_travel = False
    
    def enable_time_travel(self):
        """Enable time travel for the player."""
        self.can_time_travel = True
    
    def can_use_time_travel(self):
        """
        Check if the player can use time travel.
        
        Returns:
            bool: True if the player can use time travel, False otherwise
        """
        return self.can_time_travel and len(self.history) > 0 