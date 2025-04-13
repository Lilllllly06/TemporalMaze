class Player:
    """
    Represents the player character in the game.
    """
    
    def __init__(self, x, y):
        """
        Initialize a player at the given position.
        
        Args:
            x (int): Initial X coordinate
            y (int): Initial Y coordinate
        """
        self.x = x
        self.y = y
        self.history = []  # List of (x, y) positions
        self.max_history = 50  # Maximum number of moves to store
        
    def move(self, dx, dy, world):
        """
        Attempt to move the player by the given delta.
        
        Args:
            dx (int): X-axis movement (-1, 0, or 1)
            dy (int): Y-axis movement (-1, 0, or 1)
            world (World): The game world
            
        Returns:
            bool: True if the move was successful
        """
        # Record current position in history
        self.record_position()
        
        # Calculate new position
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check if the new position is walkable
        if world.is_walkable(new_x, new_y):
            # Check if we are stepping off a switch
            if world.get_tile(self.x, self.y) == world.SWITCH:
                world.deactivate_switch(self.x, self.y)
                
            # Update position
            self.x = new_x
            self.y = new_y
            
            # Check if we stepped on a switch
            if world.get_tile(self.x, self.y) == world.SWITCH:
                world.activate_switch(self.x, self.y)
                
            return True
        
        return False
    
    def record_position(self):
        """
        Record the current position in the history.
        """
        self.history.append((self.x, self.y))
        
        # Keep history within the maximum size
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_position(self):
        """
        Get the current position.
        
        Returns:
            tuple: (x, y) position
        """
        return (self.x, self.y)
    
    def get_history(self, steps_back=None):
        """
        Get the movement history.
        
        Args:
            steps_back (int, optional): Number of steps to get from history.
                                       If None, returns the entire history.
        
        Returns:
            list: List of (x, y) positions
        """
        if steps_back is None:
            return self.history.copy()
        
        # Return only the specified number of steps
        return self.history[-steps_back:] if steps_back <= len(self.history) else self.history.copy()
    
    def reset_history(self):
        """
        Clear the movement history.
        """
        self.history = [] 