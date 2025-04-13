import pygame

class Clone:
    """A time clone that follows a predefined path."""
    
    def __init__(self, path, start_index=0):
        """
        Initialize a clone with a path to follow.
        
        Args:
            path (list): List of positions [(x, y), ...] to follow
            start_index (int): Starting index in the path
        """
        self.path = path
        self.current_index = start_index
        self.current_position = path[start_index] if start_index < len(path) else None
        self.done = False
        
        # Create clone sprite
        self.sprite = None
        self.load_sprites()
    
    def load_sprites(self):
        """Load clone sprites."""
        # Create a simple colored square for the clone
        self.sprite = pygame.Surface((30, 30))
        self.sprite.fill((0, 200, 200))  # Cyan-ish clone
        
        # Add some visual distinction from the player
        pygame.draw.circle(self.sprite, (255, 255, 255), (15, 15), 10)
        pygame.draw.circle(self.sprite, (0, 150, 150), (15, 15), 7)
    
    def update(self, world):
        """
        Update the clone's position.
        
        Args:
            world (World): The game world
            
        Returns:
            bool: True if the clone is still active, False if it has reached the end of its path
        """
        if self.done:
            return False
        
        # Move to the next position in the path
        self.current_index += 1
        
        if self.current_index >= len(self.path):
            self.done = True
            return False
        
        # Update position
        self.current_position = self.path[self.current_index]
        
        # Check if standing on a switch
        x, y = self.current_position
        if world.get_tile(x, y) == world.SWITCH:
            world.press_switch(x, y)
        
        return True
    
    def get_position(self):
        """
        Get the clone's current position.
        
        Returns:
            tuple: Current position (x, y), or None if done
        """
        return self.current_position
    
    def render(self, screen, camera_x=0, camera_y=0):
        """
        Render the clone on the screen.
        
        Args:
            screen (pygame.Surface): The screen to render on
            camera_x (int): X-coordinate of the camera
            camera_y (int): Y-coordinate of the camera
        """
        if self.done or self.current_position is None:
            return
        
        # Calculate screen position
        tile_size = 40  # This should match World.TILE_SIZE
        screen_width, screen_height = screen.get_size()
        
        x, y = self.current_position
        screen_x = (x - camera_x) * tile_size + screen_width // 2
        screen_y = (y - camera_y) * tile_size + screen_height // 2
        
        # Center the sprite in the tile
        offset_x = (tile_size - self.sprite.get_width()) // 2
        offset_y = (tile_size - self.sprite.get_height()) // 2
        
        # Render the clone
        screen.blit(self.sprite, (screen_x + offset_x, screen_y + offset_y))


class TimeManager:
    """Manages time travel and clones."""
    
    # Constants
    MAX_CLONES = 3  # Maximum number of active clones allowed
    
    def __init__(self):
        """Initialize the time manager."""
        self.clones = []  # List of active clones
        self.time_step = 0  # Current time step
    
    def create_clone(self, player, steps_back):
        """
        Create a new clone from the player's history.
        
        Args:
            player (Player): The player object
            steps_back (int): Number of steps to go back
            
        Returns:
            bool: True if the clone was created, False otherwise
        """
        # Check if we can create more clones
        if len(self.clones) >= self.MAX_CLONES:
            return False
        
        # Get the player's history
        history = player.get_history()
        
        # Ensure there's enough history
        if steps_back > len(history):
            return False
        
        # Create a new clone starting from the selected point
        path = history[-(steps_back):]
        clone = Clone(path)
        self.clones.append(clone)
        
        return True
    
    def update_clones(self, world):
        """
        Update all active clones.
        
        Args:
            world (World): The game world
            
        Returns:
            bool: True if any clone moved, False otherwise
        """
        any_moved = False
        
        # Update each clone
        inactive_clones = []
        for i, clone in enumerate(self.clones):
            if not clone.update(world):
                inactive_clones.append(i)
            else:
                any_moved = True
        
        # Remove inactive clones (in reverse order to avoid index issues)
        for i in sorted(inactive_clones, reverse=True):
            self.clones.pop(i)
        
        self.time_step += 1
        
        return any_moved
    
    def render_clones(self, screen, camera_x=0, camera_y=0):
        """
        Render all active clones.
        
        Args:
            screen (pygame.Surface): The screen to render on
            camera_x (int): X-coordinate of the camera
            camera_y (int): Y-coordinate of the camera
        """
        for clone in self.clones:
            clone.render(screen, camera_x, camera_y)
    
    def get_clone_positions(self):
        """
        Get the positions of all active clones.
        
        Returns:
            list: List of positions [(x, y), ...]
        """
        return [clone.get_position() for clone in self.clones if clone.get_position() is not None]
    
    def get_active_clone_count(self):
        """
        Get the number of active clones.
        
        Returns:
            int: Number of active clones
        """
        return len(self.clones)
    
    def reset(self):
        """Reset the time manager."""
        self.clones = []
        self.time_step = 0 