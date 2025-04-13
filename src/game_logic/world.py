class World:
    """
    Manages the game world, including the map, objects, and their states.
    """

    # Tile type constants
    WALL = '#'
    FLOOR = '.'
    SWITCH = 'S'
    DOOR = 'D'
    EXIT = 'E'
    
    def __init__(self, map_file):
        """
        Initialize the world from a map file.
        
        Args:
            map_file (str): Path to the map file
        """
        self.map = []
        self.width = 0
        self.height = 0
        self.switches = {}  # (x, y) -> door_positions [(x1, y1), (x2, y2)]
        self.doors = {}     # (x, y) -> is_open (bool)
        self.exit_pos = None
        self.activated_switches = set()  # Set of switch positions that are activated
        
        self.load_map(map_file)
        
    def load_map(self, map_file):
        """
        Load a map from a file.
        
        Args:
            map_file (str): Path to the map file
        """
        try:
            with open(map_file, 'r') as f:
                lines = f.readlines()
                
            # Remove any trailing newlines
            lines = [line.rstrip() for line in lines]
            
            self.height = len(lines)
            if self.height > 0:
                self.width = len(lines[0])
            
            # Initialize map
            self.map = []
            for y, line in enumerate(lines):
                row = []
                for x, char in enumerate(line):
                    row.append(char)
                    
                    # Record switch and door positions
                    if char == self.SWITCH:
                        self.switches[(x, y)] = []
                    elif char == self.DOOR:
                        self.doors[(x, y)] = False  # Initially closed
                    elif char == self.EXIT:
                        self.exit_pos = (x, y)
                        
                self.map.append(row)
                
            # Simple mapping: each switch opens all doors
            # In a more complex game, you could define specific switch-door relationships
            for switch_pos in self.switches:
                self.switches[switch_pos] = list(self.doors.keys())
                
        except Exception as e:
            print(f"Error loading map: {e}")
            # Fallback to a simple map
            self.map = [['#', '#', '#'], 
                       ['#', '.', '#'], 
                       ['#', '#', '#']]
            self.width = 3
            self.height = 3
    
    def get_tile(self, x, y):
        """
        Get the tile at the specified position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            str: Tile character at the position
        """
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.map[y][x]
        return self.WALL  # Outside the map is considered a wall
    
    def is_walkable(self, x, y):
        """
        Check if a tile is walkable.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if the tile is walkable
        """
        tile = self.get_tile(x, y)
        if tile == self.WALL:
            return False
        if tile == self.DOOR and not self.doors.get((x, y), False):
            return False  # Door is closed
        return True
    
    def activate_switch(self, x, y):
        """
        Activate a switch at the specified position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        if self.get_tile(x, y) == self.SWITCH:
            self.activated_switches.add((x, y))
            # Open all doors connected to this switch
            for door_pos in self.switches.get((x, y), []):
                self.doors[door_pos] = True
    
    def deactivate_switch(self, x, y):
        """
        Deactivate a switch at the specified position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        if (x, y) in self.activated_switches:
            self.activated_switches.remove((x, y))
            # Check if any other activated switches keep the doors open
            doors_to_close = set(self.switches.get((x, y), []))
            
            # Keep doors open if any other active switch controls them
            for switch_pos in self.activated_switches:
                for door_pos in self.switches.get(switch_pos, []):
                    if door_pos in doors_to_close:
                        doors_to_close.remove(door_pos)
            
            # Close doors that are no longer activated by any switch
            for door_pos in doors_to_close:
                self.doors[door_pos] = False
    
    def is_exit(self, x, y):
        """
        Check if the position is the exit.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if the position is the exit
        """
        return self.get_tile(x, y) == self.EXIT
    
    def render_map(self, player_pos, clone_positions=None):
        """
        Render the map as a string.
        
        Args:
            player_pos (tuple): Player position (x, y)
            clone_positions (list): List of clone positions [(x, y), ...]
            
        Returns:
            str: String representation of the map
        """
        if clone_positions is None:
            clone_positions = []
            
        result = []
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                if (x, y) == player_pos:
                    row += '@'  # Player symbol
                elif (x, y) in clone_positions:
                    row += '*'  # Clone symbol
                else:
                    tile = self.get_tile(x, y)
                    # Show open doors differently
                    if tile == self.DOOR and self.doors.get((x, y), False):
                        row += '/'  # Open door symbol
                    else:
                        row += tile
            result.append(row)
        return '\n'.join(result) 