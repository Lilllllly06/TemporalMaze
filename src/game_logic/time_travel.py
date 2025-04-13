class TimeClone:
    """
    Represents a time clone that follows a predetermined path.
    """
    
    def __init__(self, start_pos, path):
        """
        Initialize a time clone.
        
        Args:
            start_pos (tuple): Starting position (x, y)
            path (list): List of positions [(x, y), ...] that the clone will follow
        """
        self.x, self.y = start_pos
        self.path = path.copy()
        self.current_step = 0
        self.is_active = True
    
    def update(self, world):
        """
        Update the clone's position based on its path.
        
        Args:
            world (World): The game world
            
        Returns:
            bool: True if the clone is still active, False if it has completed its path
        """
        if not self.is_active or self.current_step >= len(self.path):
            self.is_active = False
            return False
        
        # Check if we are stepping off a switch
        if world.get_tile(self.x, self.y) == world.SWITCH:
            world.deactivate_switch(self.x, self.y)
        
        # Move to the next position in the path
        self.x, self.y = self.path[self.current_step]
        self.current_step += 1
        
        # Check if we stepped on a switch
        if world.get_tile(self.x, self.y) == world.SWITCH:
            world.activate_switch(self.x, self.y)
        
        return True
    
    def get_position(self):
        """
        Get the current position of the clone.
        
        Returns:
            tuple: (x, y) position
        """
        return (self.x, self.y)


class TimeManager:
    """
    Manages time travel and clones.
    """
    
    def __init__(self, max_clones=2):
        """
        Initialize the time manager.
        
        Args:
            max_clones (int): Maximum number of clones allowed at once
        """
        self.clones = []
        self.max_clones = max_clones
    
    def create_clone(self, player, steps_back):
        """
        Create a new time clone based on the player's history.
        
        Args:
            player (Player): The player object
            steps_back (int): How many steps to go back in time
            
        Returns:
            bool: True if the clone was created, False otherwise
        """
        if len(self.clones) >= self.max_clones:
            return False
        
        history = player.get_history(steps_back)
        if not history:
            return False
        
        # Create a new clone starting at the first position in the history
        clone = TimeClone(history[0], history)
        self.clones.append(clone)
        return True
    
    def update_clones(self, world):
        """
        Update all active clones.
        
        Args:
            world (World): The game world
        """
        # Update each clone and remove inactive ones
        self.clones = [clone for clone in self.clones if clone.update(world)]
    
    def get_clone_positions(self):
        """
        Get the positions of all active clones.
        
        Returns:
            list: List of (x, y) positions
        """
        return [clone.get_position() for clone in self.clones]
    
    def reset(self):
        """
        Reset the time manager by removing all clones.
        """
        self.clones = [] 