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
        for clone in self.clones:
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
                # Toggle debug info with F3
                if event.key == pygame.K_F3:
                    self.show_debug = not self.show_debug
                elif event.key == pygame.K_F5:
                    # Force garbage collection
                    gc.collect()
                elif event.key == pygame.K_F2:
                    # Center camera on player (helps find lost player)
                    if self.player and self.world:
                        print(f"Centering camera on player at {self.player.x}, {self.player.y}")
                        map_width_px = self.world.width * TILE_SIZE
                        map_height_px = self.world.height * TILE_SIZE
                        
                        self.camera.x = max(0, min(self.player.x * TILE_SIZE - SCREEN_WIDTH // 2, 
                                                 map_width_px - SCREEN_WIDTH))
                        self.camera.y = max(0, min(self.player.y * TILE_SIZE - SCREEN_HEIGHT // 2, 
                                                 map_height_px - SCREEN_HEIGHT))
                        
                        # Also update visible area
                        self._update_visible_area()
                        self.show_message("Camera centered on player", 1.0)
                    
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
        """Load a level, trying procedural generation first."""
        try:
            print(f"Loading level {level_number} using procedural generation...")
            
            # Reset game state before loading/generating
            self.clones = []
            self.guards = []
            self.player = None
            self.world = None
            self.level_completed = False
            self.player_caught = False
            
            # Generate a level using the LevelGenerator
            level_data = self.level_generator.generate_level()
            
            # Setup the game state from the generated data
            success = self._setup_level_from_data(level_data)
            
            if success:
                print(f"Successfully generated and set up level {level_number}")
                return True
            else:
                print(f"Failed to set up generated level {level_number}, creating fallback.")
                return self._create_fallback_level()
                
        except Exception as e:
            print(f"Error during procedural generation for level {level_number}: {e}")
            traceback.print_exc()
            print("Falling back to simple level creation...")
            return self._create_fallback_level()

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
            terminal_pos = level_data["terminal_pos"]
            
            # Create world of appropriate size
            height, width = level_map.shape
            self.world = World(width, height)
            
            # IMPORTANT: Initialize world dictionaries
            self.world.switches = {} # Map switch_pos -> list of door_pos it affects
            self.world.doors = {}    # Map door_pos -> {required_switches: set(), is_open: bool}
            self.world.portals = {} 
            self.world.terminals = {}
            self.world.items = {}
            self.world.activated_switches = set()
            
            # Set tiles based on level map
            for y in range(height):
                for x in range(width):
                    tile_type = level_map[y][x]
                    self.world.set_tile(x, y, tile_type) # This also sets self.world.exit_pos if tile is TILE_EXIT
            
            # Set player
            player_x, player_y = player_start
            self.player = Player(player_x, player_y)
            self.player.world = self.world 
            
            # --- Process switches and doors --- 
            # Initialize doors first, using the structure from level_data
            self.world.doors = door_data_dict
            
            # Initialize switches and link them to the doors they control
            for switch_pos in switch_positions:
                self.world.switches[switch_pos] = [] # Initialize empty list for doors controlled by this switch
                
            # Iterate through doors to find which switches control them
            for door_pos, data in door_data_dict.items():
                # Ensure door tile is set correctly (it might have been set by map loop, but double check)
                self.world.set_tile(door_pos[0], door_pos[1], TILE_DOOR_CLOSED)
                # Populate the switch -> doors mapping
                for required_switch in data["required_switches"]:
                    if required_switch in self.world.switches:
                        self.world.switches[required_switch].append(door_pos)
                    else:
                         print(f"Warning: Door {door_pos} requires switch {required_switch} which doesn't exist in switch list.")
                         # Ensure the switch exists on the map even if missed in the list
                         self.world.set_tile(required_switch[0], required_switch[1], TILE_SWITCH)
                         self.world.switches[required_switch] = [door_pos] # Create entry

            # --- Process other elements --- 
            
            # Set up portals
            for portal_a, portal_b in portal_pairs:
                self.world.portals[portal_a] = portal_b
                self.world.portals[portal_b] = portal_a
                # Ensure tiles are correct (might be redundant if map was accurate)
                self.world.set_tile(portal_a[0], portal_a[1], TILE_PORTAL_A)
                self.world.set_tile(portal_b[0], portal_b[1], TILE_PORTAL_B)
            
            # Add guards
            for guard_pos in guard_start_positions:
                guard_x, guard_y = guard_pos
                guard = Guard(guard_x, guard_y)
                
                # Set up patrol route (simple back-and-forth if switches exist)
                if switch_positions:
                    target_pos = random.choice(switch_positions)
                    guard.patrol_route = [(guard_x, guard_y), target_pos, (guard_x, guard_y)]
                else:
                    guard.patrol_route = [(guard_x, guard_y)]
                self.guards.append(guard)
            
            # Add items
            for item_pos, item_type in item_data_list:
                self.world.items[item_pos] = item_type
                # Ensure tile is correct
                self.world.set_tile(item_pos[0], item_pos[1], item_type)
            
            # Set terminal
            if terminal_pos:
                self.world.terminals[terminal_pos] = "Hint: Two switches are sometimes better than one... especially when you can be in two places at once (Press T)."
                # Ensure tile is correct
                self.world.set_tile(terminal_pos[0], terminal_pos[1], TILE_TERMINAL)
            
            # Update camera position
            self._update_camera()
            
            # Call initial door update in case some start activated (unlikely but safe)
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
                self.state = STATE_RULES # Go to rules/help screen

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