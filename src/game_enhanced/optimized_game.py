"""
Optimized version of the main Game class.
Addresses potential performance bottlenecks that could cause freezing.
"""

import pygame
import time
import math
import random
import gc
import os
import traceback
from .constants import *
from .assets import assets
from .world import World
from .entities import Player, TimeClone, Guard, Terminal
from .level_generator import LevelGenerator, load_level_from_file

# Import the original Game class to inherit from
from .game import Game as OriginalGame

class Camera:
    """Camera that follows the player with smoother movement."""
    def __init__(self, screen_width, screen_height):
        self.x = 0
        self.y = 0
        self.width = screen_width
        self.height = screen_height

class OptimizedGame(OriginalGame):
    """Optimized version of the Game class with performance improvements."""
    
    def __init__(self):
        """Initialize the optimized game."""
        # Initialize pygame with hardware acceleration if available
        pygame.init()
        
        # Try to enable hardware acceleration (may not be available on all systems)
        os.environ['SDL_RENDERER_DRIVER'] = 'opengl'
        
        # Use double buffering
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
        
        # Set up clock with fixed framerate
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MAIN_MENU
        self.previous_state = STATE_MAIN_MENU # Store state before pause/help
        
        # Game objects
        self.world = None
        self.player = None
        self.clones = []
        self.guards = []
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Optimization: Use a render cache to avoid redrawing static elements
        self.render_cache = {}
        self.cache_valid = False
        
        # Optimization: Track visible area for culling
        self.visible_area = (0, 0, 0, 0)  # (x, y, width, height) in tile coordinates
        
        # Game state variables
        self.current_level = 1
        self.level_completed = False
        self.player_caught = False
        self.time_travel_steps = 0
        self.dt = 0  # Delta time for updates
        self.message = None
        self.message_timer = 0
        
        # Movement control
        self.last_move_time = 0
        self.movement_delay = MOVEMENT_DELAY
        
        # UI elements
        self.font = assets.get_font("medium")
        self.title_font = assets.get_font("title")
        
        # Procedural level generation
        self.level_generator = LevelGenerator(50, 50)
        
        # Load built-in levels
        self.built_in_levels = []
        self._load_built_in_levels()
        
        # Time travel input state
        self.time_travel_input = ""
        self.time_travel_prompt = None
        
        # Debug info
        self.show_debug = False
        self.frame_times = []
        self.last_gc_time = time.time()
        
        # Rules screen state
        self.rules_scroll_offset = 0
        self.rules_lines = [
            "OBJECTIVE:",
            "Navigate through time-bending mazes to reach the exit portal.",
            "",
            "GAMEPLAY:",
            "- Move: WASD or Arrow Keys.",
            "- Avoid Guards: They will capture you!",
            "- Collect Keys: To unlock doors.",
            "- Use Terminals (E): For hints and story.",
            "- Collect Potions: Restore time travel energy.",
            "",
            "TIME TRAVEL (T Key):",
            "- Create a clone that repeats your past movements.",
            "- Use clones to activate multiple switches.",
            "- Costs Energy (shown top-left).",
            "",
            "OTHER CONTROLS:",
            "- R: Restart level",
            "- ESC: Pause / Unpause / Back",
            "- H: View this help screen",
            "- E: Interact with Switches/Terminals",
            "- F3: Toggle Debug Info"
        ]
    
    def run(self):
        """
        Main game loop with improved performance monitoring.
        Adds garbage collection and prevents potential infinite loops.
        """
        # Safety check - initialize if needed
        if not self.player or not self.world:
            print("Game not properly initialized, creating fallback level")
            self._create_fallback_level()
        
        # Set maximum FPS
        MAX_FRAME_TIME = 1.0 / 30  # Cap at 30 FPS minimum
        last_frame_time = time.time()
        frame_count = 0
        
        while self.running:
            # Measure frame time
            current_time = time.time()
            frame_time = current_time - last_frame_time
            
            # Store frame time for debug display
            self.frame_times.append(frame_time)
            if len(self.frame_times) > 60:
                self.frame_times.pop(0)
            
            # Run periodic garbage collection to prevent memory buildup
            if current_time - self.last_gc_time > 5.0:
                gc.collect()
                self.last_gc_time = current_time
            
            # Ensure we don't get stuck in an infinite loop
            if frame_time > MAX_FRAME_TIME * 10:
                print(f"WARNING: Frame took too long: {frame_time:.4f}s. Enforcing cap.")
                frame_time = MAX_FRAME_TIME
            
            # Catch errors in the main loop
            try:
                # Process events, update game state and render
                self.handle_events()
                
                # Calculate delta time for physics/movement updates
                self.dt = min(frame_time, MAX_FRAME_TIME)  # Cap delta time to prevent physics issues
                self.update()
                
                # Only render at target framerate
                self.render()
            except Exception as e:
                print(f"Error in main game loop: {e}")
                traceback.print_exc()
                print("Attempting to continue...")
            
            # Tick the clock
            self.clock.tick(FPS)
            
            # Update frame time
            last_frame_time = current_time
            frame_count += 1
        
        pygame.quit()
    
    def _update_visible_area(self):
        """Update the currently visible area for culling."""
        if not self.player:
            return
            
        # Calculate visible area in tile coordinates
        tile_width = SCREEN_WIDTH // TILE_SIZE + 2  # Add padding
        tile_height = SCREEN_HEIGHT // TILE_SIZE + 2
        
        # Center on player
        center_x = self.player.x
        center_y = self.player.y
        
        # Calculate bounds
        world_width = self.world.width if self.world else 50
        world_height = self.world.height if self.world else 50
        
        # Calculate corners (with bounds checking)
        left = max(0, min(center_x - tile_width // 2, world_width - tile_width))
        top = max(0, min(center_y - tile_height // 2, world_height - tile_height))
        
        # Store visible area
        self.visible_area = (left, top, tile_width, tile_height)
    
    def is_visible(self, x, y):
        """Check if a tile is in the visible area."""
        left, top, width, height = self.visible_area
        return (left <= x < left + width and 
                top <= y < top + height)
    
    def update(self):
        """Update game state with performance optimizations."""
        # Get delta time
        self.dt = min(self.clock.get_time() / 1000.0, 0.1)  # Cap at 100ms to prevent issues
        
        try:
            if self.state == STATE_PLAYING:
                # Handle player movement with delay
                current_time = time.time()
                keys = pygame.key.get_pressed()
                dx, dy = 0, 0
                
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    dy = -1
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    dy = 1
                elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    dx = -1
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    dx = 1
                    
                if (dx != 0 or dy != 0) and current_time - self.last_move_time > self.movement_delay:
                    if self.player:  # Make sure player exists
                        # Invalidate render cache when player moves
                        self.cache_valid = False
                        self.player.move(dx, dy, self.world)
                        self.last_move_time = current_time
                
                # Update clones with improved performance
                active_clones = []
                for clone in self.clones:
                    if clone.update(self):
                        active_clones.append(clone)
                
                # This is more efficient than repeatedly popping from the list
                self.clones = active_clones
                
                # Update guards
                for guard in self.guards:
                    guard.update(self)
                    
                # Update player paw prints
                if self.player:
                    self.player.update(self)
                
                # Update camera to follow player
                if self.player:
                    self._update_camera()
                
                # Check for level completion
                if self.world and getattr(self.world, 'level_completed', False):
                    self.state = STATE_LEVEL_COMPLETE
                    
                # Check for player being caught
                if self.player_caught:
                    self.state = STATE_GAME_OVER
                
            # Update message timer
            if self.message and self.message_timer > 0:
                self.message_timer -= self.dt
                if self.message_timer <= 0:
                    self.message = None
                
        except Exception as e:
            # Print error but don't crash
            print(f"Error in game update: {e}")
            traceback.print_exc()
    
    def render(self):
        """Render the game with performance optimizations."""
        try:
            # Clear screen with background color
            self.screen.fill(BG_COLOR)
            
            # Adjust camera position to center on player before rendering anything
            if self.state in [STATE_PLAYING, STATE_PAUSED, STATE_LEVEL_COMPLETE, STATE_GAME_OVER] and self.player:
                # Camera is already updated in update method, don't force position here
                pass
            
            if self.state == STATE_MAIN_MENU:
                self._render_main_menu()
            elif self.state == STATE_RULES:
                self._render_rules()
            elif self.state in [STATE_PLAYING, STATE_PAUSED, STATE_TIME_TRAVEL, STATE_DIALOGUE]:
                self._render_game_optimized()
                
                if self.state == STATE_PAUSED:
                    self._render_pause_menu()
                elif self.state == STATE_DIALOGUE:
                    self._render_dialogue_box()
                elif self.state == STATE_TIME_TRAVEL:
                    self._render_time_travel_prompt()
            elif self.state == STATE_LEVEL_COMPLETE:
                self._render_game_optimized()
                self._render_level_complete()
            elif self.state == STATE_GAME_OVER:
                self._render_game_optimized()
                self._render_game_over()
            
            # Always render messages if there are any
            if self.message:
                self._render_message()
            
            # Render debug info if enabled
            if self.show_debug:
                self._render_debug_info()
                
                # Display additional camera and player positioning info in debug mode
                if self.player and self.world:
                    debug_font = pygame.font.SysFont("monospace", 16)
                    pos_text = f"Player: ({self.player.x}, {self.player.y}) | Camera: ({self.camera.x//TILE_SIZE}, {self.camera.y//TILE_SIZE})"
                    text = debug_font.render(pos_text, True, (255, 255, 255))
                    self.screen.blit(text, (15, 95))
            
            pygame.display.flip()
            
        except Exception as e:
            # Print error but don't crash
            print(f"Error in game rendering: {e}")
            traceback.print_exc()
    
    def _render_game_optimized(self):
        """Optimized version of the game rendering with culling."""
        # Only render if we have a world
        if not self.world:
            return
        
        # Render the world (only visible tiles)
        self._render_visible_world()
        
        # Render entities only if in visible area
        self._render_visible_entities()
        
        # Render UI (always visible)
        self._render_ui()
    
    def _render_visible_world(self):
        """Render only the visible portion of the world."""
        if not self.world:
            return
        
        # Draw a background grid only for areas outside the map bounds
        for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
            for x in range(0, SCREEN_WIDTH, TILE_SIZE):
                # Calculate world coordinates for this screen position
                world_x = x + self.camera.x
                world_y = y + self.camera.y
                
                # Calculate world tile coordinates 
                world_tile_x = int(world_x // TILE_SIZE)
                world_tile_y = int(world_y // TILE_SIZE)
                
                # Only draw grid for areas outside the map
                if (world_tile_x < 0 or world_tile_x >= self.world.width or
                    world_tile_y < 0 or world_tile_y >= self.world.height):
                    # Draw light grid lines
                    pygame.draw.rect(self.screen, (DOGGY_BEIGE[0]-10, DOGGY_BEIGE[1]-10, DOGGY_BEIGE[2]-10), 
                                   (x, y, TILE_SIZE, TILE_SIZE), 1)
            
        # Get screen dimensions in tiles
        screen_tiles_width = SCREEN_WIDTH // TILE_SIZE + 2  # Add padding
        screen_tiles_height = SCREEN_HEIGHT // TILE_SIZE + 2
        
        # Calculate the visible range in tile coordinates based on camera position
        camera_tile_x = int(self.camera.x // TILE_SIZE)
        camera_tile_y = int(self.camera.y // TILE_SIZE)
        
        # Calculate visible range
        start_x = max(0, camera_tile_x)
        start_y = max(0, camera_tile_y)
        end_x = min(self.world.width, camera_tile_x + screen_tiles_width)
        end_y = min(self.world.height, camera_tile_y + screen_tiles_height)
        
        # Render all visible tiles
        for y in range(int(start_y), int(end_y)):
            for x in range(int(start_x), int(end_x)):
                # Skip tiles outside world bounds
                if x < 0 or y < 0 or x >= self.world.width or y >= self.world.height:
                    continue
                
                # Get tile type at this position
                tile_type = self.world.get_tile_at(x, y)
                
                # Skip empty tiles
                if tile_type is None:
                    continue
                
                # Get tile image
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
                else:
                    # Unknown tile type, default to floor
                    image = assets.get_image("floor")
                
                # Calculate screen position directly
                screen_x = x * TILE_SIZE - int(self.camera.x)
                screen_y = y * TILE_SIZE - int(self.camera.y)
                
                # Render the tile if it's within the screen bounds
                if (-TILE_SIZE < screen_x < SCREEN_WIDTH and 
                    -TILE_SIZE < screen_y < SCREEN_HEIGHT):
                    self.screen.blit(image, (screen_x, screen_y))
    
    def _render_visible_entities(self):
        """Render only entities that are in the visible area."""
        
        def get_screen_pos(entity_x, entity_y):
            """Helper function to calculate screen position."""
            return (int(entity_x * TILE_SIZE - self.camera.x),
                    int(entity_y * TILE_SIZE - self.camera.y))

        # Draw a target indicator around the player
        if self.player:
            player_screen_x, player_screen_y = get_screen_pos(self.player.x, self.player.y)
            # Draw a highlight around the player's position
            highlight_size = TILE_SIZE + 6
            highlight_rect = (
                player_screen_x - 3,
                player_screen_y - 3,
                highlight_size,
                highlight_size
            )
            pygame.draw.rect(self.screen, (255, 255, 0, 128), highlight_rect, 2)
        
        # Render paw prints for player
        if self.player and hasattr(self.player, 'paw_prints'):
            for paw in self.player.paw_prints:
                screen_x, screen_y = get_screen_pos(paw["x"], paw["y"])
                frame = assets.get_animation_frame("paw_prints", paw["frame"])
                self.screen.blit(frame, (screen_x, screen_y))
        
        # Render clones and their paw prints
        print(f"[Render] Clones list size: {len(self.clones)}") # DEBUG: Check if clones exist before rendering
        for clone in self.clones:
            print(f"[Render] Rendering Clone at ({clone.x}, {clone.y}), Active: {getattr(clone, 'active', 'N/A')}, Step: {getattr(clone, 'current_step', 'N/A')}") # DEBUG
            # Render clone's paw prints if they exist
            if hasattr(clone, 'paw_prints'):
                for paw in clone.paw_prints:
                    screen_x, screen_y = get_screen_pos(paw["x"], paw["y"])
                    frame = assets.get_animation_frame("paw_prints", paw["frame"])
                    # Make clone paw prints slightly different color
                    paw_frame = frame.copy()
                    paw_frame.fill((150, 150, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
                    self.screen.blit(paw_frame, (screen_x, screen_y))
            
            # Render clones
            screen_x, screen_y = get_screen_pos(clone.x, clone.y)
            # Get clone direction safely
            direction = getattr(clone, 'facing', 'right')
            self.screen.blit(assets.get_image("clone", direction), (screen_x, screen_y))
        
        # Render guards
        for guard in self.guards:
            screen_x, screen_y = get_screen_pos(guard.x, guard.y)
            # Choose image based on guard state
            if guard.state == GUARD_ALERTED:
                image = assets.get_image("guard_alerted")
            else:
                image = assets.get_image("guard")
            self.screen.blit(image, (screen_x, screen_y))
        
        # Always render player last so it's on top
        if self.player:
            player_screen_x, player_screen_y = get_screen_pos(self.player.x, self.player.y)
            # Get player direction safely
            direction = getattr(self.player, 'facing', 'right')
            self.screen.blit(assets.get_image("player", direction), (player_screen_x, player_screen_y))
    
    def _render_debug_info(self):
        """Render debug information overlay."""
        if not self.frame_times:
            return
            
        # Calculate FPS
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        current_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        # Create debug text
        debug_lines = [
            f"FPS: {current_fps:.1f}",
            f"Objects: P:{1 if self.player else 0} C:{len(self.clones)} G:{len(self.guards)}",
            f"State: {self.state}",
            f"Visible: {self.visible_area}"
        ]
        
        # Create background
        debug_height = len(debug_lines) * 20 + 10
        debug_bg = pygame.Surface((250, debug_height), pygame.SRCALPHA)
        debug_bg.fill((0, 0, 0, 180))
        self.screen.blit(debug_bg, (10, 10))
        
        # Render text
        debug_font = pygame.font.SysFont("monospace", 16)
        for i, line in enumerate(debug_lines):
            text = debug_font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (15, 15 + i * 20))
    
    def handle_events(self):
        """Handle user input events with additional debug controls."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                # Handle global keys first (like debug)
                if event.key == pygame.K_F3:
                    self.show_debug = not self.show_debug
                elif event.key == pygame.K_F5:
                    gc.collect()
                elif event.key == pygame.K_F2:
                    # Center camera logic...
                    pass # Assume this logic is correct
                
                # Handle state-specific input
                if self.state == STATE_MAIN_MENU:
                    self._handle_main_menu_input(event.key)
                elif self.state == STATE_PLAYING:
                    self._handle_playing_input(event.key)
                elif self.state == STATE_PAUSED:
                    self._handle_paused_input(event.key)
                elif self.state == STATE_TIME_TRAVEL:
                    self._handle_time_travel_input(event.key)
                elif self.state == STATE_LEVEL_COMPLETE:
                    self._handle_level_complete_input(event.key)
                elif self.state == STATE_GAME_OVER:
                    self._handle_game_over_input(event.key)
                elif self.state == STATE_DIALOGUE:
                    self._handle_dialogue_input(event.key)
                elif self.state == STATE_RULES:
                    self._handle_rules_input(event.key)
                    
    def _handle_time_travel_input(self, key):
        """Handle input when in time travel state."""
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYING
            self.time_travel_prompt = None
            print("Cancelled time travel.")
        elif key == pygame.K_RETURN:
            if self.time_travel_input:
                try:
                    steps = int(self.time_travel_input)
                    max_steps = len(self.player.history) - 1 if self.player and hasattr(self.player, 'history') else 0
                    if 1 <= steps <= max_steps:
                         # Perform time travel
                        if self.player.time_travel(steps, self):
                            self.show_message(f"Time traveled back {steps} steps!", 2)
                        else:
                             self.show_message("Could not time travel!", 2)
                    else:
                        self.show_message(f"Invalid steps. Enter 1-{max_steps}", 2)
                except ValueError:
                    self.show_message("Invalid input. Enter numbers only.", 2)
                except AttributeError:
                     self.show_message("Player history not available.", 2)
                    
                # Exit time travel state regardless of success
                self.state = STATE_PLAYING
                self.time_travel_prompt = None
                self.time_travel_input = ""
            else:
                self.show_message("Enter number of steps first.", 1.5)
        elif key == pygame.K_BACKSPACE:
            self.time_travel_input = self.time_travel_input[:-1]
        # Handle number input (0-9) using key codes
        elif pygame.K_0 <= key <= pygame.K_9:
             # Limit input length (e.g., max 3 digits)
            if len(self.time_travel_input) < 3:
                # Convert key code to digit character
                digit = chr(key)
                self.time_travel_input += digit
            else:
                self.show_message("Maximum steps input reached.", 1)

    def _load_built_in_levels(self):
        """Initialize an empty list of built-in levels."""
        # Create at least one built-in level to prevent list index errors
        self.built_in_levels = []
        
        # Add one sample built-in level
        print("Initializing built-in levels...")
        try:
            # Create a basic fallback level structure
            width = (SCREEN_WIDTH // TILE_SIZE) + 4
            height = (SCREEN_HEIGHT // TILE_SIZE) + 2
            
            # This is a placeholder level data structure
            simple_level = {
                "width": width,
                "height": height,
                "player_start": (2, 2),
                "exit": (width-3, height-3),
                "switches": [],
                "doors": [],
                "portals": [],
                "guards": [],
                "items": []
            }
            self.built_in_levels.append(simple_level)
            print(f"Added 1 built-in level. Total levels: {len(self.built_in_levels)}")
        except Exception as e:
            print(f"Error setting up built-in levels: {e}")
            traceback.print_exc()
            # Ensure we have at least an empty list
            self.built_in_levels = []

    def load_level(self, level_number):
        """Load a level, trying specific files first, then procedural gen."""
        # Reset game state before loading/generating
        self.clones = []
        self.guards = []
        self.player = None
        self.world = None
        self.level_completed = False
        self.player_caught = False
        
        level_loaded = False
        level_data = None
        
        # --- Try loading specific level file --- 
        level_file_path = f"maps/level{level_number}.txt"
        if os.path.exists(level_file_path):
            try:
                print(f"Loading level {level_number} from file: {level_file_path}")
                level_data = load_level_from_file(level_file_path) # Assumes this helper exists
                if level_data:
                     # We need to convert the file format to the dictionary format expected by _setup_level
                    converted_data = self._convert_file_data_to_dict(level_data)
                    if self._setup_level_from_data(converted_data):
                        level_loaded = True
                    else:
                         print(f"Error setting up level from file data: {level_file_path}")
                else:
                     print(f"Helper function load_level_from_file returned None for {level_file_path}")
            except Exception as e:
                print(f"Error loading or setting up level file {level_file_path}: {e}")
                traceback.print_exc()
        else:
            print(f"Level file not found: {level_file_path}. Trying procedural generation.")

        # --- If file loading failed, try procedural generation --- 
        if not level_loaded:
            try:
                print(f"Generating procedural level {level_number}...")
                level_data = self.level_generator.generate_level()
                if self._setup_level_from_data(level_data):
                    print(f"Successfully generated and set up level {level_number}")
                    level_loaded = True
                else:
                    print(f"Failed to set up generated level {level_number}.")
            except Exception as e:
                print(f"Error during procedural generation for level {level_number}: {e}")
                traceback.print_exc()

        # --- Fallback if everything else failed --- 
        if not level_loaded:
            print("All loading methods failed. Creating fallback level.")
            return self._create_fallback_level() # Returns True/False
            
        return True # If we got here, loading succeeded somehow

    def _convert_file_data_to_dict(self, file_level_data):
        """Converts data loaded from file (likely tuple) to the dictionary format."""
        try:
             map_array, p_start, switch_list, door_list, portal_list, guard_list, item_list, term_list_from_file = file_level_data
             height, width = map_array.shape
             
             exit_pos = None
             terminals = {}
             for y in range(height):
                 for x in range(width):
                     if map_array[y][x] == TILE_EXIT:
                         exit_pos = (x, y)
                     elif map_array[y][x] == TILE_TERMINAL:
                         terminals[(x,y)] = f"Terminal ({x},{y})" 
             if exit_pos is None: print("Warning: No Exit found!")

             # Assign tutorial text to specific terminal locations for ultra-simple map
             term_pos = None 
             if (6, 1) in terminals: terminals[(6, 1)] = "WASD/Arrows=Move. O=Potion(Energy), K=Key."
             if (9, 3) in terminals: terminals[(9, 3)] = "Switches (S) open Doors (D)."
             if (4, 8) in terminals: terminals[(4, 8)] = "Door (C) needs 2 Switches (T)? Press T for clone help!"
             # Removed X3 terminal as space is tight
             if terminals: term_pos = list(terminals.keys())[-1] 

             # Convert doors - Add conditional logic for tutorial level 1
             door_dict = {}
             if level_number == 1: # Specific linking for level 1 map
                 # Use KNOWN positions from maps/level1.txt directly
                 switch_S_pos = (3, 3)
                 switch_T1_pos = (4, 7) # Assuming this is the first 'T' found/processed
                 switch_T2_pos = (11, 7) # Assuming this is the second 'T'
                 door_D_pos = (6, 3)
                 door_C_pos = (6, 7)
                 door_L_pos = (8, 1)
                 
                 # Verify these items actually exist in the loaded lists 
                 # (as a sanity check, though load_level_from_file should provide them)
                 all_found_switches = set(switch_list)
                 all_found_doors = set(door_list)
                 
                 # Build the door dictionary using known positions and links
                 if door_D_pos in all_found_doors and switch_S_pos in all_found_switches:
                     door_dict[door_D_pos] = {"required_switches": {switch_S_pos}, "is_open": False}
                 elif door_D_pos in all_found_doors: # Door exists but switch doesn't?
                      print(f"[Level 1 Load Warning] Door D found at {door_D_pos}, but required switch S at {switch_S_pos} missing from file data.")
                      door_dict[door_D_pos] = {"required_switches": set(), "is_open": False} # Add door anyway
                      
                 if door_C_pos in all_found_doors and switch_T1_pos in all_found_switches and switch_T2_pos in all_found_switches:
                     door_dict[door_C_pos] = {"required_switches": {switch_T1_pos, switch_T2_pos}, "is_open": False}
                 elif door_C_pos in all_found_doors: # Door exists but switches don't?
                      print(f"[Level 1 Load Warning] Door C found at {door_C_pos}, but required switches T at {switch_T1_pos}/{switch_T2_pos} missing from file data.")
                      door_dict[door_C_pos] = {"required_switches": set(), "is_open": False}
                      
                 if door_L_pos in all_found_doors:
                     door_dict[door_L_pos] = {"required_switches": set(), "is_open": False} # Key door
                 else:
                     print(f"[Level 1 Load Warning] Locked door L expected at {door_L_pos} not found in file data.")

                 print(f"[Level 1 Load] Linked doors based on known positions: {door_dict}")
             else:
                 # Original logic for non-level 1 maps (no specific links assumed)
                 for door_pos in door_list:
                     door_dict[door_pos] = {"required_switches": set(), "is_open": False}

             # The rest of the conversion logic remains the same...
             # linked_switches = {} # This was commented out correctly before

             converted = {
                "width": width, "height": height, "map": map_array,
                "player_start": p_start, "exit_pos": exit_pos,
                "switches": switch_list, # Pass the list of switch positions found
                "doors": door_dict,       # Pass the dict of doors with empty requirements
                "portals": portal_list, "guards": guard_list, "items": item_list,
                "terminal_pos": term_pos, "terminals": terminals
             }
             return converted
        except Exception as e:
             print(f"Error converting file data: {e}")
             traceback.print_exc()
             return None

    def _create_fallback_level(self):
        """Create a very simple fallback level that should work in any case."""
        try:
            print("Creating simple fallback level")
            
            # Create a world that fills the screen
            width = (SCREEN_WIDTH // TILE_SIZE) + 4
            height = (SCREEN_HEIGHT // TILE_SIZE) + 2
            self.world = World(width, height)
            
            # Fill with floor tiles, walls around the edge
            for x in range(width):
                for y in range(height):
                    if x == 0 or y == 0 or x == width-1 or y == height-1:
                        self.world.set_tile(x, y, TILE_WALL)
                    else:
                        self.world.set_tile(x, y, TILE_FLOOR)
            
            # Initialize world data structures
            self.world.switches = {}
            self.world.doors = {}
            self.world.portals_a = {}
            self.world.portals_b = {}
            self.world.terminals = {}
            
            # Place player and exit in opposite corners
            self.world.set_tile(1, 1, TILE_FLOOR)
            self.player = Player(1, 1)
            # Set player's world reference explicitly
            self.player.world = self.world
            
            self.world.set_tile(width-2, height-2, TILE_EXIT)
            
            # Reset collections
            self.guards = []
            self.clones = []
            
            # Initialize camera with our new method
            self._update_camera()
            
            print("Fallback level created successfully")
            print(f"Player at (1, 1), Camera at ({self.camera.x}, {self.camera.y})")
            print(f"World size: {width}x{height} tiles, Screen size: {SCREEN_WIDTH//TILE_SIZE}x{SCREEN_HEIGHT//TILE_SIZE} tiles")
            
            # Return success
            return True
        except Exception as e:
            print(f"ERROR even in creating fallback level: {e}")
            traceback.print_exc()
            
            # Last resort
            return self._bare_minimum_level()

    def _update_camera(self):
        """Update camera position to follow the player."""
        if not self.player or not self.world:
            return
        
        # Calculate target camera position
        # Center the camera on the player
        target_x = self.player.x * TILE_SIZE - SCREEN_WIDTH // 2 + TILE_SIZE // 2
        target_y = self.player.y * TILE_SIZE - SCREEN_HEIGHT // 2 + TILE_SIZE // 2
        
        # Calculate the max camera position to prevent showing empty space beyond map bounds
        max_camera_x = max(0, (self.world.width * TILE_SIZE) - SCREEN_WIDTH)
        max_camera_y = max(0, (self.world.height * TILE_SIZE) - SCREEN_HEIGHT)
        
        # Clamp camera position to ensure the map fills the screen when possible
        target_x = max(0, min(target_x, max_camera_x))
        target_y = max(0, min(target_y, max_camera_y))
        
        # Apply camera movement with smooth transition
        camera_speed = 0.1
        self.camera.x += (target_x - self.camera.x) * camera_speed
        self.camera.y += (target_y - self.camera.y) * camera_speed
        
        # Update visible area
        self._update_visible_area() 

    def _setup_level_from_data(self, level_data):
        """Set up a level from the provided level data dictionary."""
        try:
            # Reset game state
            self.clones = []
            self.guards = []
            self.player = None
            self.world = None
            self.level_completed = False
            self.player_caught = False
            
            # --- Unpack data from the dictionary --- 
            level_map = level_data["map"]
            player_start = level_data["player_start"]
            switch_positions = level_data["switches"] # List of switch (x, y)
            door_data_dict = level_data["doors"] # Dict of door_pos -> {required_switches: set(), ...}
            portal_pairs = level_data["portals"]
            guard_start_positions = level_data["guards"]
            item_data_list = level_data["items"]
            terminal_data = level_data.get("terminals", {}) # Use the new terminals dict
            
            # Create world of appropriate size
            height, width = level_map.shape
            self.world = World(width, height)
            
            # IMPORTANT: Initialize world dictionaries
            self.world.switches = {} # Map switch_pos -> list of door_pos it affects
            self.world.doors = {}    # Map door_pos -> {required_switches: set(), is_open: bool}
            self.world.portals = {} 
            self.world.terminals = {} # Initialize world's terminals
            self.world.items = {}
            self.world.activated_switches = set()
            
            # Set tiles based on level map
            for y in range(height):
                for x in range(width):
                    tile_type = level_map[y][x]
                    self.world.set_tile(x, y, tile_type) 
            
            # Set player
            player_x, player_y = player_start
            self.player = Player(player_x, player_y)
            self.player.world = self.world 
            self.player.game_ref = self # Give player reference to game to show messages
            
            # --- Process switches and doors --- 
            self.world.doors = door_data_dict
            for switch_pos in switch_positions:
                self.world.switches[switch_pos] = [] 
            for door_pos, data in door_data_dict.items():
                self.world.set_tile(door_pos[0], door_pos[1], TILE_DOOR_CLOSED)
                for required_switch in data["required_switches"]:
                    if required_switch in self.world.switches:
                        self.world.switches[required_switch].append(door_pos)
                    else:
                         print(f"Warning: Door {door_pos} requires switch {required_switch} which doesn't exist in switch list.")
                         self.world.set_tile(required_switch[0], required_switch[1], TILE_SWITCH)
                         self.world.switches[required_switch] = [door_pos] 

            # --- Process other elements --- 
            # Set up portals
            for portal_a, portal_b in portal_pairs:
                self.world.portals[portal_a] = portal_b
                self.world.portals[portal_b] = portal_a
                self.world.set_tile(portal_a[0], portal_a[1], TILE_PORTAL_A)
                self.world.set_tile(portal_b[0], portal_b[1], TILE_PORTAL_B)
            
            # Add guards
            for guard_pos in guard_start_positions:
                guard_x, guard_y = guard_pos
                guard = Guard(guard_x, guard_y)
                if switch_positions:
                    target_pos = random.choice(switch_positions)
                    guard.patrol_route = [(guard_x, guard_y), target_pos, (guard_x, guard_y)]
                else:
                    guard.patrol_route = [(guard_x, guard_y)]
                self.guards.append(guard)
            
            # Add items
            for item_pos, item_type in item_data_list:
                self.world.items[item_pos] = item_type
                self.world.set_tile(item_pos[0], item_pos[1], item_type)
            
            # Set terminals using the new dictionary
            self.world.terminals = terminal_data
            for term_pos in terminal_data:
                 self.world.set_tile(term_pos[0], term_pos[1], TILE_TERMINAL)
            
            # Update camera position
            self._update_camera()
            
            # Call initial door update
            self.world._update_doors()
            
            return True
        except KeyError as e:
            print(f"Error setting up level from data: Missing key {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"Error setting up level from data: {e}")
            traceback.print_exc()
            return False

    def _start_game(self):
        """Start a new game with error handling."""
        try:
            print("Starting new game...")
            self.state = STATE_PLAYING
            self.current_level = 1
            self.player_caught = False
            self.level_completed = False
            
            # Load the initial level
            print("Loading initial level...")
            self.load_level(self.current_level)
        except Exception as e:
            print(f"Error starting game: {e}")
            traceback.print_exc()
            
            # Create a basic fallback level as last resort
            print("Creating emergency fallback level due to start game error...")
            self._bare_minimum_level()

    def _bare_minimum_level(self):
        """Create the absolute minimum level with no dependencies."""
        try:
            print("Creating bare minimum emergency level")
            
            # Create a tiny world
            width, height = 10, 10
            self.world = World(width, height)
            
            # Just a border of walls and floor inside
            for x in range(width):
                for y in range(height):
                    if x == 0 or y == 0 or x == width-1 or y == height-1:
                        self.world.set_tile(x, y, TILE_WALL)
                    else:
                        self.world.set_tile(x, y, TILE_FLOOR)
            
            # Initialize world data structures
            self.world.switches = {}
            self.world.doors = {}
            self.world.portals_a = {}
            self.world.portals_b = {}
            self.world.terminals = {}
            
            # Player at center
            self.player = Player(5, 5)
            self.player.world = self.world
            
            # Exit near corner
            self.world.set_tile(8, 8, TILE_EXIT)
            
            # Empty collections
            self.guards = []
            self.clones = []
            
            # Initialize camera
            self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.camera.x = 0
            self.camera.y = 0
            
            # Done
            print("Emergency level created successfully")
            return True
            
        except Exception as e:
            print(f"CRITICAL ERROR in emergency level: {e}")
            traceback.print_exc()
            # If this fails, there's no recovery
            self.running = False
            return False 

    def _handle_playing_input(self, key):
        """Handle input when the game is actively playing."""
        if self.player:
            if key == pygame.K_t:
                # Initiate time travel input
                self.state = STATE_TIME_TRAVEL
                self.time_travel_input = ""
                # Construct prompt message with max steps
                max_steps = len(self.player.history) - 1 if self.player and hasattr(self.player, 'history') else 0
                self.time_travel_prompt = f"Steps back (1-{max_steps}): " 
                print(f"Entering Time Travel state. Prompt: {self.time_travel_prompt}") # Debug
            elif key == pygame.K_r:
                self.restart_level()
            elif key == pygame.K_ESCAPE:
                self.state = STATE_PAUSED
            elif key == pygame.K_i:
                # Placeholder for inventory (if implemented)
                self.show_message("Inventory not implemented yet.", 1.5)
            elif key == pygame.K_e:
                # Interact with adjacent tiles (terminals, switches)
                self.player.interact(self)
            elif key == pygame.K_h:
                self.previous_state = self.state # Store current state
                self.state = STATE_RULES 

    def _render_time_travel_prompt(self):
        """Render the input prompt for time travel steps."""
        if not self.time_travel_prompt:
            return
            
        # Create a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) 
        self.screen.blit(overlay, (0, 0))
        
        # Define prompt box dimensions and position
        box_width = 400
        box_height = 150
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        
        # Draw prompt box background
        pygame.draw.rect(self.screen, UI_BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, UI_HIGHLIGHT, (box_x, box_y, box_width, box_height), 3)
        
        # Render prompt text
        prompt_text_surface = self.font.render(self.time_travel_prompt, True, UI_TEXT)
        prompt_rect = prompt_text_surface.get_rect(center=(box_x + box_width // 2, box_y + 40))
        self.screen.blit(prompt_text_surface, prompt_rect)
        
        # Render current input text
        input_text_surface = self.font.render(self.time_travel_input, True, UI_TEXT)
        input_rect = input_text_surface.get_rect(center=(box_x + box_width // 2, box_y + 80))
        self.screen.blit(input_text_surface, input_rect)
        
        # Blinking cursor effect
        if int(time.time() * 2) % 2 == 0: # Blink roughly every half second
            cursor_x = input_rect.right + 5
            cursor_y = input_rect.top
            cursor_height = input_rect.height
            pygame.draw.line(self.screen, UI_TEXT, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)
            
        # Instructions
        instr_font = assets.get_font("small")
        instr_text = instr_font.render("Enter numbers, BACKSPACE to delete, ENTER to confirm, ESC to cancel", True, UI_TEXT)
        instr_rect = instr_text.get_rect(center=(box_x + box_width // 2, box_y + box_height - 20))
        self.screen.blit(instr_text, instr_rect) 

    def _render_ui(self):
        """Render the game UI (overrides base class version)."""
        # UI background panel
        ui_background = pygame.Surface((SCREEN_WIDTH, 130), pygame.SRCALPHA)
        ui_background.fill(UI_BG)
        self.screen.blit(ui_background, (0, 0))
        
        # Draw border for UI panel
        pygame.draw.line(self.screen, UI_HIGHLIGHT, (0, 130), (SCREEN_WIDTH, 130), 2)
        
        # Draw doggy logo in UI
        self._draw_doggy_logo(SCREEN_WIDTH // 2 - 80, 10, 30)
        
        # Add UI panel decorations (paw prints)
        for i in range(3):
            x_pos = 30 + i * 300
            y_pos = 15
            self._draw_decorative_paw(x_pos, y_pos, DOGGY_BROWN, 15)
            self._draw_decorative_paw(SCREEN_WIDTH - x_pos, y_pos, DOGGY_BROWN, 15)
        
        # Info boxes with bone borders
        info_box_width = SCREEN_WIDTH // 4 - 20
        
        # Level indicator box
        self._draw_bone_box(10, 40, info_box_width, 80)
        level_text = self.font.render(f"Level: {self.current_level}", True, UI_TEXT)
        self.screen.blit(level_text, (20, 50))
        
        # Energy indicator box
        self._draw_bone_box(info_box_width + 20, 40, info_box_width, 80)
        # Ensure player exists before accessing attributes
        player_energy = self.player.energy if self.player else 0
        player_energy_max = self.player.energy_max if self.player else PLAYER_START_ENERGY
        energy_text = self.font.render(f"Energy: {player_energy}/{player_energy_max}", True, UI_TEXT)
        self.screen.blit(energy_text, (info_box_width + 30, 50))
        
        # Draw energy bones (visual indicator)
        for i in range(player_energy_max):
            bone_x = info_box_width + 30 + i * 25
            bone_y = 75
            bone_color = DOGGY_BROWN if i < player_energy else DOGGY_BEIGE
            self._draw_mini_bone(bone_x, bone_y, 20, bone_color)
        
        # Clone and keys box
        self._draw_bone_box(info_box_width*2 + 30, 40, info_box_width, 80)
        
        player_keys = self.player.keys if self.player else 0
        keys_text = self.font.render(f"Keys: {player_keys}", True, UI_TEXT)
        self.screen.blit(keys_text, (info_box_width*2 + 40, 50))
        
        # Draw key bones
        for i in range(player_keys):
            key_x = info_box_width*2 + 100 + i * 20
            key_y = 55
            self._draw_mini_bone(key_x, key_y, 15, DOGGY_YELLOW)
        
        # --- Clone Count --- 
        clone_count = len(self.clones)
        clones_text = self.font.render(f"Clones: {clone_count}", True, UI_TEXT)
        self.screen.blit(clones_text, (info_box_width*2 + 40, 80))
        
        # Draw clone indicators (small pawprints)
        max_clones_display = 3 # Example: limit displayed paws
        for i in range(min(clone_count, max_clones_display)):
            paw_x = info_box_width*2 + 100 + i * 20
            paw_y = 85
            self._draw_decorative_paw(paw_x, paw_y, DOGGY_BLUE, 10)
        
        # Controls reminder at bottom
        controls_bg = pygame.Surface((SCREEN_WIDTH, 36), pygame.SRCALPHA)
        controls_bg.fill(UI_BG)
        self.screen.blit(controls_bg, (0, SCREEN_HEIGHT - 36))
        
        pygame.draw.line(self.screen, UI_HIGHLIGHT, (0, SCREEN_HEIGHT - 36), (SCREEN_WIDTH, SCREEN_HEIGHT - 36), 2)
        
        controls_text = self.font.render("WASD: Move | T: Time Travel | R: Restart | ESC: Pause | H: Help", True, UI_TEXT)
        controls_x = (SCREEN_WIDTH - controls_text.get_width()) // 2
        self.screen.blit(controls_text, (controls_x, SCREEN_HEIGHT - 30))

    def _draw_bone_box(self, x, y, width, height):
        # Basic placeholder if not inheriting properly
        pygame.draw.rect(self.screen, UI_BG, (x,y,width,height))
        pygame.draw.rect(self.screen, UI_HIGHLIGHT, (x,y,width,height), 1)
        pass 

    def _draw_mini_bone(self, x, y, size, color):
        pygame.draw.circle(self.screen, color, (x, y), size // 4)
        pass

    def _draw_decorative_paw(self, x, y, color, size):
        pygame.draw.circle(self.screen, color, (x, y), size // 2)
        pass
        
    def _draw_doggy_logo(self, x, y, size):
        pygame.draw.circle(self.screen, DOGGY_BROWN, (x + size, y + size), size)
        pass 

    def _handle_rules_input(self, key):
        """Handle input on the rules screen, including scrolling."""
        if key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
            self.state = self.previous_state # Return to previous state
            self.rules_scroll_offset = 0 # Reset scroll on exit
        elif key == pygame.K_UP:
            self.rules_scroll_offset = max(0, self.rules_scroll_offset - 1)
        elif key == pygame.K_DOWN:
            # Calculate max scroll based on screen height and font size
            # Ensure font is loaded before getting line height
            line_height = self.font.get_linesize() if self.font else 25
            text_area_height = SCREEN_HEIGHT - 150 # Approximate text area height
            visible_lines = text_area_height // line_height
            max_scroll = max(0, len(self.rules_lines) - visible_lines)
            self.rules_scroll_offset = min(max_scroll, self.rules_scroll_offset + 1)
            
    def _render_rules(self):
        """Render the game rules screen with scrolling."""
        self.screen.fill(BG_COLOR)
        
        # Ensure fonts are loaded
        title_font = assets.get_font("title")
        medium_font = assets.get_font("medium")
        small_font = assets.get_font("small")
        # Use a default if medium isn't found, though it should be
        bold_font = assets.get_font("medium_bold") if assets.get_font("medium_bold") else medium_font 
        
        if not title_font or not medium_font or not small_font:
             print("Error: Rules fonts not loaded!")
             # Optionally draw an error message on screen
             error_text = pygame.font.SysFont(None, 30).render("Error loading fonts for rules!", True, (255,0,0))
             self.screen.blit(error_text, (50, 100))
             # Attempt to use default system font
             title_font = pygame.font.SysFont(None, FONT_TITLE)
             medium_font = pygame.font.SysFont(None, FONT_MEDIUM)
             small_font = pygame.font.SysFont(None, FONT_SMALL)
             bold_font = pygame.font.SysFont(None, FONT_MEDIUM, bold=True)

        # Title
        title = title_font.render("GAME RULES & HELP", True, DARK_BLUE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)
        
        # Define text area
        text_area_y = title_rect.bottom + 30
        text_area_height = SCREEN_HEIGHT - text_area_y - 60 
        line_height = medium_font.get_linesize()
        visible_lines_count = text_area_height // line_height
        
        # Determine which lines to display
        start_index = self.rules_scroll_offset
        end_index = min(len(self.rules_lines), start_index + visible_lines_count)
        display_lines = self.rules_lines[start_index:end_index]
        
        # Render visible lines
        y_pos = text_area_y
        for line in display_lines:
            text_color = UI_TEXT
            text_x = 100
            font_to_use = medium_font
            is_header = ":" in line and line.endswith(":") and not line.startswith("-")
            is_control = line.strip().startswith("-")

            if is_header:
                text_color = UI_HIGHLIGHT
                text_x = 80
                font_to_use = bold_font 
            elif is_control:
                 text_x = 120 # Indent controls
                 font_to_use = medium_font
            else:
                 font_to_use = medium_font
            
            # Add wrapping for longer lines if needed (simple version)
            max_width = SCREEN_WIDTH - text_x - 50 # Leave margin
            words = line.split(' ')
            lines_to_render = []
            current_line = ""
            for word in words:
                 test_line = current_line + word + " "
                 test_surface = font_to_use.render(test_line, True, text_color)
                 if test_surface.get_width() < max_width:
                      current_line = test_line
                 else:
                      lines_to_render.append(current_line)
                      current_line = word + " "
            lines_to_render.append(current_line) # Add the last line
                
            # Render the potentially wrapped lines
            for render_line in lines_to_render:
                 if y_pos + line_height > text_area_y + text_area_height: # Prevent drawing below text area
                     break 
                 text = font_to_use.render(render_line.strip(), True, text_color)
                 self.screen.blit(text, (text_x, y_pos))
                 y_pos += line_height
            if y_pos + line_height > text_area_y + text_area_height:
                break # Stop rendering if we overflowed the area
            
        # Draw Scroll indicators
        indicator_x = SCREEN_WIDTH - 30
        if self.rules_scroll_offset > 0:
            pygame.draw.polygon(self.screen, UI_HIGHLIGHT, 
                                [(indicator_x - 10, text_area_y + 10),
                                 (indicator_x, text_area_y),
                                 (indicator_x + 10, text_area_y + 10)])
                                 
        if end_index < len(self.rules_lines):
            bottom_y = text_area_y + text_area_height
            pygame.draw.polygon(self.screen, UI_HIGHLIGHT, 
                                [(indicator_x - 10, bottom_y - 10),
                                 (indicator_x, bottom_y),
                                 (indicator_x + 10, bottom_y - 10)])
        
        # Return to menu instruction
        back_text = medium_font.render("Press ESC to return", True, UI_HIGHLIGHT)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self.screen.blit(back_text, back_rect)

    def _handle_level_complete_input(self, key):
        """Handle input when a level is completed (override)."""
        if key == pygame.K_RETURN:
            print(f"[Level Complete] Transitioning from level {self.current_level}...")
            self.current_level += 1
            self.level_completed = False # Reset flag
            self.player_caught = False # Reset flag
            
            # Load the next level using the correct method
            success = self.load_level(self.current_level)
            
            if success:
                print(f"[Level Complete] Successfully loaded level {self.current_level}.")
                self.state = STATE_PLAYING
            else:
                # If loading fails, go back to main menu instead of restarting level 1
                print(f"[Level Complete] Failed to load level {self.current_level}. Returning to main menu.")
                self.state = STATE_MAIN_MENU 
                self.show_message(f"Error loading level {self.current_level}!", 3.0)
                self.current_level = 1 # Reset for next game start 

    def _handle_paused_input(self, key):
        """Handle input when game is paused."""
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYING # Resume
        elif key == pygame.K_q:
            self.state = STATE_MAIN_MENU # Quit to menu
        elif key == pygame.K_h:
            self.previous_state = self.state # Store paused state
            self.state = STATE_RULES
            
    def _handle_main_menu_input(self, key):
        """Handle input when in the main menu."""
        # Minimal implementation
        if key == pygame.K_RETURN:
             self._start_game()
        elif key == pygame.K_h:
             self.previous_state = self.state
             self.state = STATE_RULES
        elif key == pygame.K_q:
             self.running = False

    def _handle_game_over_input(self, key):
        """Handle input when the game is over."""
        if key == pygame.K_RETURN:
            self.restart_level()
        elif key == pygame.K_q:
            self.state = STATE_MAIN_MENU

    def _handle_dialogue_input(self, key):
        """Handle input when in dialogue state."""
        # Minimal implementation - just return to previous state
        if key == pygame.K_RETURN or key == pygame.K_SPACE or key == pygame.K_ESCAPE:
            self.state = self.previous_state 
            self.message = None # Clear potential dialogue message

    def show_message(self, message, duration=2.0):
        # Keep this one as it's used directly in OptimizedGame logic
        self.message = message
        self.message_timer = duration
        
    def restart_level(self):
        # Keep this one
        print("Restarting level...")
        self.load_level(self.current_level)