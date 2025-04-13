"""
Procedural level generator for Temporal Maze.
"""

import random
import numpy as np
from .constants import *

class Room:
    """Represents a room in the procedurally generated level."""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.connected = False
    
    @property
    def center(self):
        """Get the center coordinates of the room."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def intersects(self, other):
        """Check if this room intersects with another room."""
        return (self.x <= other.x + other.width and
                self.x + self.width >= other.x and
                self.y <= other.y + other.height and
                self.y + self.height >= other.y)
    
    def get_rect(self):
        """Get the rectangle representation of the room."""
        return (self.x, self.y, self.width, self.height)

class LevelGenerator:
    """Generates procedural levels for the game."""
    
    def __init__(self, width=50, height=50):
        """
        Initialize the level generator.
        
        Args:
            width (int): Width of the level in tiles
            height (int): Height of the level in tiles
        """
        self.width = width
        self.height = height
        
    def generate_level(self, min_rooms=MIN_ROOMS, max_rooms=MAX_ROOMS):
        """
        Generate a procedural level, ensuring at least one puzzle requires time clones.
        
        Returns:
            dict: level_data containing map, player_start, switches, doors, etc.
        """
        # Initialize the level with walls
        level_map = np.full((self.height, self.width), TILE_WALL, dtype=int)
        
        # Generate rooms
        rooms = self._generate_rooms(min_rooms, max_rooms)
        if not rooms or len(rooms) < 3: # Need at least 3 rooms for a good clone puzzle
            print("Not enough rooms generated, falling back to simple level.")
            return self._generate_simple_level()
        
        # Place rooms on the map
        for room in rooms:
            for y in range(room.y + 1, room.y + room.height - 1):
                for x in range(room.x + 1, room.x + room.width - 1):
                    if 0 <= y < self.height and 0 <= x < self.width:
                        level_map[y][x] = TILE_FLOOR
        
        # Connect rooms with corridors
        self._connect_rooms(rooms, level_map)
        
        # Place special tiles
        player_start = rooms[0].center
        exit_pos = rooms[-1].center
        level_map[exit_pos[1]][exit_pos[0]] = TILE_EXIT
        
        # Prepare data structures for level elements
        switches = [] # List of (x, y) positions
        doors = {}    # Dict mapping door_pos -> {required_switches: set(), is_open: False}
        portals = []  # List of ((ax, ay), (bx, by)) pairs
        guards = []   # List of (x, y) start positions
        items = []    # List of ((x, y), item_type)
        terminal_pos = None
        
        # --- Create the mandatory time-clone puzzle --- 
        clone_puzzle_created = False
        max_attempts = 10
        for _ in range(max_attempts):
            # Select two distinct rooms (not start or end) that are reasonably far apart
            possible_rooms = rooms[1:-1]
            if len(possible_rooms) < 2:
                break # Cannot create puzzle
            
            room1, room2 = random.sample(possible_rooms, 2)
            dist_sq = (room1.center[0] - room2.center[0])**2 + (room1.center[1] - room2.center[1])**2
            min_dist_sq = (MIN_CLONE_SWITCH_DISTANCE)**2
            
            if dist_sq < min_dist_sq:
                continue # Rooms too close, try again
                
            # Find positions for switches in these rooms
            switch1_pos = self._find_empty_position_in_room(room1, level_map, TILE_FLOOR)
            switch2_pos = self._find_empty_position_in_room(room2, level_map, TILE_FLOOR)
            
            # Find a position for the door, preferably blocking the path to the exit
            door_pos = self._find_path_position(random.choice([room1, room2]), exit_pos, level_map)
            
            if switch1_pos and switch2_pos and door_pos:
                # Add switches
                switches.append(switch1_pos)
                switches.append(switch2_pos)
                level_map[switch1_pos[1]][switch1_pos[0]] = TILE_SWITCH
                level_map[switch2_pos[1]][switch2_pos[0]] = TILE_SWITCH
                
                # Add door and link it to *both* switches
                level_map[door_pos[1]][door_pos[0]] = TILE_DOOR_CLOSED
                doors[door_pos] = {"required_switches": {switch1_pos, switch2_pos}, "is_open": False}
                
                clone_puzzle_created = True
                print(f"Created time-clone puzzle: Door at {door_pos} requires switches {switch1_pos} and {switch2_pos}")
                break # Mandatory puzzle created
        
        if not clone_puzzle_created:
            print("Failed to create mandatory time-clone puzzle, falling back to simple level.")
            return self._generate_simple_level()
            
        # --- Add optional additional elements (single switches, portals, etc.) --- 
        
        # Add optional single-switch doors
        num_extra_doors = random.randint(0, min(2, len(rooms) // 3))
        available_rooms = [r for r in rooms if r != rooms[0] and r != rooms[-1]]
        for _ in range(num_extra_doors):
            if not available_rooms: break
            switch_room = random.choice(available_rooms)
            available_rooms.remove(switch_room)
            switch_pos = self._find_empty_position_in_room(switch_room, level_map, TILE_FLOOR)
            if not switch_pos or switch_pos in switches: continue
            
            if not available_rooms: break
            door_room = random.choice(available_rooms)
            door_target = random.choice([player_start, exit_pos])
            door_pos = self._find_path_position(door_room, door_target, level_map)
            
            if switch_pos and door_pos and door_pos not in doors:
                switches.append(switch_pos)
                level_map[switch_pos[1]][switch_pos[0]] = TILE_SWITCH
                level_map[door_pos[1]][door_pos[0]] = TILE_DOOR_CLOSED
                # Single required switch
                doors[door_pos] = {"required_switches": {switch_pos}, "is_open": False}
                
        # Place portals (same logic as before)
        if random.random() < 0.7:  # 70% chance to include portals
            portal_attempts = 0
            num_portal_pairs = 0
            while num_portal_pairs < 2 and portal_attempts < 10:
                portal_attempts += 1
                if len(rooms) > 2:
                    portal_rooms = random.sample([r for r in rooms[1:-1]], 2)
                    pos_a = self._find_empty_position_in_room(portal_rooms[0], level_map, TILE_FLOOR)
                    pos_b = self._find_empty_position_in_room(portal_rooms[1], level_map, TILE_FLOOR)
                    
                    # Check if positions are already used or are None
                    if pos_a and pos_b and level_map[pos_a[1]][pos_a[0]] == TILE_FLOOR and level_map[pos_b[1]][pos_b[0]] == TILE_FLOOR:
                        portals.append((pos_a, pos_b))
                        level_map[pos_a[1]][pos_a[0]] = TILE_PORTAL_A
                        level_map[pos_b[1]][pos_b[0]] = TILE_PORTAL_B
                        num_portal_pairs += 1
        
        # Place guards (same logic as before)
        num_guards = random.randint(0, min(3, len(rooms) - 1))
        guard_candidate_rooms = [r for r in rooms[1:] if r.center != exit_pos]
        for _ in range(num_guards):
            if not guard_candidate_rooms: break
            guard_room = random.choice(guard_candidate_rooms)
            guard_candidate_rooms.remove(guard_room) # Ensure guards are in different rooms
            guard_pos = self._find_empty_position_in_room(guard_room, level_map, TILE_FLOOR)
            if guard_pos and level_map[guard_pos[1]][guard_pos[0]] == TILE_FLOOR:
                guards.append(guard_pos)
                # Don't place on map - entity system handles this
        
        # Place items (same logic as before)
        num_items = random.randint(1, min(5, len(rooms) - 1))
        item_candidate_rooms = [r for r in rooms[1:] if r.center != exit_pos]
        for _ in range(num_items):
            if not item_candidate_rooms: break
            item_room = random.choice(item_candidate_rooms)
            item_pos = self._find_empty_position_in_room(item_room, level_map, TILE_FLOOR)
            if item_pos and level_map[item_pos[1]][item_pos[0]] == TILE_FLOOR:
                item_type = TILE_ITEM_KEY if random.random() < 0.3 else TILE_ITEM_POTION # More potions than keys
                items.append((item_pos, item_type))
                level_map[item_pos[1]][item_pos[0]] = item_type
                # Prevent placing multiple items in the exact same spot
                item_candidate_rooms.remove(item_room) 
        
        # Place terminal (optional)
        if random.random() < 0.5: # 50% chance of a terminal
             terminal_candidate_rooms = [r for r in rooms[1:-1]]
             if terminal_candidate_rooms:
                terminal_room = random.choice(terminal_candidate_rooms)
                t_pos = self._find_empty_position_in_room(terminal_room, level_map, TILE_FLOOR)
                if t_pos and level_map[t_pos[1]][t_pos[0]] == TILE_FLOOR:
                    level_map[t_pos[1]][t_pos[0]] = TILE_TERMINAL
                    terminal_pos = t_pos
        
        # Return data as dictionary for clarity
        level_data = {
            "width": self.width,
            "height": self.height,
            "map": level_map, 
            "player_start": player_start,
            "exit_pos": exit_pos,
            "switches": switches, # Just the positions
            "doors": doors,       # Dict with positions and required switches
            "portals": portals, 
            "guards": guards,     # Just the positions
            "items": items,
            "terminal_pos": terminal_pos
        }
        return level_data
    
    def _generate_rooms(self, min_rooms, max_rooms):
        """Generate random non-overlapping rooms."""
        rooms = []
        num_rooms = random.randint(min_rooms, max_rooms)
        max_attempts = 100
        
        for _ in range(num_rooms):
            attempts = 0
            while attempts < max_attempts:
                # Random room size
                w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
                h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
                
                # Random position
                x = random.randint(1, self.width - w - 1)
                y = random.randint(1, self.height - h - 1)
                
                new_room = Room(x, y, w, h)
                
                # Check if it overlaps with other rooms
                if all(not new_room.intersects(other) for other in rooms):
                    rooms.append(new_room)
                    break
                
                attempts += 1
        
        return rooms
    
    def _connect_rooms(self, rooms, level_map):
        """Connect rooms with corridors."""
        if not rooms:
            return
        
        # Set the first room as connected
        rooms[0].connected = True
        
        # Connect each unconnected room to a connected room
        for room in rooms[1:]:
            if not room.connected:
                # Find the closest connected room
                connected_rooms = [r for r in rooms if r.connected]
                if not connected_rooms:
                    # Fallback if no rooms are connected
                    room.connected = True
                    continue
                
                closest_room = min(connected_rooms, 
                                   key=lambda r: ((r.center[0] - room.center[0])**2 + 
                                                 (r.center[1] - room.center[1])**2))
                
                # Connect the rooms with a corridor
                self._create_corridor(room.center, closest_room.center, level_map)
                room.connected = True
    
    def _create_corridor(self, start, end, level_map):
        """Create an L-shaped corridor between two points."""
        x1, y1 = start
        x2, y2 = end
        
        # Decide on horizontal-first or vertical-first
        if random.random() < 0.5:
            # Horizontal then vertical
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= y1 < self.height and 0 <= x < self.width:
                    level_map[y1][x] = TILE_FLOOR
                    
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= y < self.height and 0 <= x2 < self.width:
                    level_map[y][x2] = TILE_FLOOR
        else:
            # Vertical then horizontal
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= y < self.height and 0 <= x1 < self.width:
                    level_map[y][x1] = TILE_FLOOR
                    
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= y2 < self.height and 0 <= x < self.width:
                    level_map[y2][x] = TILE_FLOOR
    
    def _find_empty_position_in_room(self, room, level_map, target_tile):
        """Find an empty position in a room matching the target tile."""
        positions = []
        for y in range(room.y + 1, room.y + room.height - 1):
            for x in range(room.x + 1, room.x + room.width - 1):
                if 0 <= y < self.height and 0 <= x < self.width and level_map[y][x] == target_tile:
                    positions.append((x, y))
        
        if positions:
            return random.choice(positions)
        else:
            return None
    
    def _find_path_position(self, room, target, level_map):
        """Find a position along a path between a room and a target."""
        room_center = room.center
        x1, y1 = room_center
        x2, y2 = target
        
        # Get positions along the corridor
        positions = []
        
        # Check horizontal path
        for x in range(min(x1, x2) + 1, max(x1, x2)):
            if 0 <= y1 < self.height and 0 <= x < self.width and level_map[y1][x] == TILE_FLOOR:
                positions.append((x, y1))
                
        # Check vertical path
        for y in range(min(y1, y2) + 1, max(y1, y2)):
            if 0 <= y < self.height and 0 <= x2 < self.width and level_map[y][x2] == TILE_FLOOR:
                positions.append((x2, y))
        
        if positions:
            return random.choice(positions)
        else:
            # Fallback to any floor tile near the room
            for dist in range(1, 10):
                for y in range(y1 - dist, y1 + dist + 1):
                    for x in range(x1 - dist, x1 + dist + 1):
                        if (0 <= y < self.height and 0 <= x < self.width and 
                            level_map[y][x] == TILE_FLOOR and
                            (x != x1 or y != y1)):  # Not the center itself
                            positions.append((x, y))
                if positions:
                    return random.choice(positions)
            
            return None
    
    def _generate_simple_level(self):
        """
        Generate a simple fallback level if procedural generation fails.
        Returns the same tuple format as generate_level.
        """
        # Create a simple 20x20 level with a central room
        level_map = np.full((20, 20), TILE_WALL, dtype=int)
        
        # Central room
        for y in range(5, 15):
            for x in range(5, 15):
                level_map[y][x] = TILE_FLOOR
        
        # Player start
        player_start = (7, 7)
        
        # Exit
        level_map[12][12] = TILE_EXIT
        
        # Switch and door
        switch_pos = (9, 7)
        level_map[switch_pos[1]][switch_pos[0]] = TILE_SWITCH
        
        door_pos = (10, 10)
        level_map[door_pos[1]][door_pos[0]] = TILE_DOOR_CLOSED
        
        # Return in the same format as generate_level
        return {
            "width": self.width,
            "height": self.height,
            "map": level_map,
            "player_start": player_start,
            "exit_pos": (12, 12),
            "switches": [switch_pos],
            "doors": {door_pos: {"required_switches": {switch_pos}, "is_open": False}},
            "portals": [],
            "guards": [],
            "items": [],
            "terminal_pos": None
        }

TILE_MAPPING = {
    '#': TILE_WALL,
    '.': TILE_FLOOR,
    'P': TILE_FLOOR, # Player start is floor
    'E': TILE_EXIT,
    'S': TILE_SWITCH,
    'T': TILE_SWITCH, # Use T for time-travel switches
    'D': TILE_DOOR_CLOSED,
    'L': TILE_DOOR_CLOSED, # Locked door
    'C': TILE_DOOR_CLOSED, # Clone door
    'A': TILE_PORTAL_A,
    'B': TILE_PORTAL_B,
    'K': TILE_ITEM_KEY,
    'O': TILE_ITEM_POTION, # Use O for potion (P is player)
    'X': TILE_TERMINAL,
    'G': TILE_FLOOR # Guard start is floor
}

def load_level_from_file(file_path):
    """Loads level data from a text file.

    Args:
        file_path (str): Path to the level file.

    Returns:
        tuple: (map_array, player_start, switches, doors, portals, guards, items, terminal_pos) 
               or None if loading fails.
    """
    try:
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            print(f"Error: Level file {file_path} is empty.")
            return None
            
        height = len(lines)
        width = len(lines[0])
        
        level_map = np.full((height, width), TILE_FLOOR, dtype=int)
        player_start = None
        switches = []
        doors = []
        portals = {}
        portal_list = [] # Store pairs
        guards = []
        items = []
        terminal_pos = None

        for y, line in enumerate(lines):
            if len(line) != width:
                 print(f"Error: Inconsistent line width in {file_path} at line {y+1}.")
                 return None
            for x, char in enumerate(line):
                pos = (x, y)
                tile_type = TILE_MAPPING.get(char, TILE_FLOOR) # Default to floor
                level_map[y][x] = tile_type
                
                if char == 'P': player_start = pos
                elif char == 'S' or char == 'T': switches.append(pos)
                elif char == 'D' or char == 'L' or char == 'C': doors.append(pos)
                elif char == 'A': portals['A'] = pos
                elif char == 'B': portals['B'] = pos
                elif char == 'K': items.append((pos, TILE_ITEM_KEY))
                elif char == 'O': items.append((pos, TILE_ITEM_POTION))
                elif char == 'X': terminal_pos = pos
                elif char == 'G': guards.append(pos)

        if not player_start:
            print(f"Warning: No player start 'P' found in {file_path}. Placing at (1,1).")
            player_start = (1, 1)
            level_map[1][1] = TILE_FLOOR # Ensure start is walkable
            
        # Pair up portals
        if 'A' in portals and 'B' in portals:
            portal_list.append((portals['A'], portals['B']))
        elif 'A' in portals or 'B' in portals:
             print(f"Warning: Unpaired portal found in {file_path}. Portals disabled.")

        # Important: Return doors as a list of positions, not the dict needed by World
        # The conversion happens in OptimizedGame._convert_file_data_to_dict
        return (level_map, player_start, switches, doors, portal_list, guards, items, terminal_pos)

    except FileNotFoundError:
        print(f"Error: Level file not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading level file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None 