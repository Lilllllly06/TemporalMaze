"""
Constants for the Temporal Maze game.
"""

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TITLE = "Temporal Maze: A Time-Traveling Puzzle Adventure"

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (230, 230, 230)
BLUE = (0, 122, 255)
DARK_BLUE = (0, 51, 102)
RED = (255, 59, 48)
MINT = (0, 199, 190, 200)  # With alpha for overlay
LAVENDER = (191, 148, 228, 200)  # With alpha for overlay

# Doggy theme colors
DOGGY_BROWN = (165, 113, 78)  # Light brown
DOGGY_DARK_BROWN = (115, 77, 38)  # Dark brown 
DOGGY_BEIGE = (255, 235, 205)  # Beige/tan color
DOGGY_PINK = (255, 182, 193)  # Light pink for nose/tongue
DOGGY_BLACK = (40, 40, 40)  # Soft black for paws/nose
DOGGY_BLUE = (86, 151, 211)  # Collar blue
DOGGY_GREEN = (121, 189, 143)  # Mint green
DOGGY_YELLOW = (255, 222, 125)  # Golden/yellow

# UI colors
BG_COLOR = DOGGY_BEIGE  # Light beige background
UI_BG = (DOGGY_BEIGE[0], DOGGY_BEIGE[1], DOGGY_BEIGE[2], 220)  # Semi-transparent beige
UI_HIGHLIGHT = DOGGY_BROWN  # Brown highlight
UI_TEXT = DOGGY_DARK_BROWN  # Dark brown text

# Font settings
FONT_SMALL = 16
FONT_MEDIUM = 20
FONT_LARGE = 24
FONT_TITLE = 36

# Game settings
TILE_SIZE = 32
FPS = 60
MAX_CLONES = 3
MAX_HISTORY = 100
MOVEMENT_DELAY = 0.2  # Delay between movements in seconds

# Tile types (now using integers for easier handling in Pygame)
TILE_WALL = 0
TILE_FLOOR = 1
TILE_SWITCH = 2
TILE_DOOR_CLOSED = 3
TILE_DOOR_OPEN = 4
TILE_EXIT = 5
TILE_PORTAL_A = 6
TILE_PORTAL_B = 7
TILE_ITEM_KEY = 8
TILE_ITEM_POTION = 9
TILE_TERMINAL = 10
TILE_GUARD = 11

# Game states
STATE_MAIN_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_LEVEL_COMPLETE = 3
STATE_GAME_OVER = 4
STATE_TIME_TRAVEL = 5
STATE_DIALOGUE = 6
STATE_RULES = 7

# Direction constants
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Guard states
GUARD_PATROLLING = 0
GUARD_ALERTED = 1
GUARD_CHASING = 2

# Procedural generation parameters
MIN_ROOM_SIZE = 5
MAX_ROOM_SIZE = 15
MIN_ROOMS = 5
MAX_ROOMS = 10
CORRIDOR_WIDTH = 1
MIN_CLONE_SWITCH_DISTANCE = 10 # Minimum distance (in tiles) between switches for a time-clone puzzle

# Player settings
PLAYER_START_ENERGY = 3

# ... existing code ... 