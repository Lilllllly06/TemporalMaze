"""
Main game class for the enhanced Temporal Maze.
"""

import os
import pygame
import time
import math
import random
from .constants import *
from .assets import assets
from .world import World
from .entities import Player, TimeClone, Guard, Terminal
from .level_generator import LevelGenerator, load_level_from_file

class Camera:
    """Camera class for following the player."""
    
    def __init__(self, width, height):
        """
        Initialize the camera.
        
        Args:
            width (int): View width
            height (int): View height
        """
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        
    def apply(self, entity):
        """
        Apply camera offset to an entity position.
        
        Args:
            entity: Entity with x, y coordinates
            
        Returns:
            tuple: Screen position (x, y)
        """
        # Convert from tile coordinates to pixel coordinates, then adjust for camera position
        screen_x = entity.x * TILE_SIZE - self.x
        screen_y = entity.y * TILE_SIZE - self.y
        return (screen_x, screen_y)
        
    def update(self, target):
        """
        Update camera position to follow a target.
        
        Args:
            target: Entity to follow
        """
        # Check if target is valid
        if not target:
            return
        
        # Calculate the center position of the screen in pixels
        screen_center_x = SCREEN_WIDTH // 2
        screen_center_y = SCREEN_HEIGHT // 2
        
        # Calculate the target position in pixels
        target_px_x = target.x * TILE_SIZE
        target_px_y = target.y * TILE_SIZE
        
        # Center the camera on the target
        # We want the target to be at the center of the screen, so:
        # target_px_x - camera.x = screen_center_x
        # Therefore:
        self.x = target_px_x - screen_center_x
        self.y = target_px_y - screen_center_y
        
        # Safely get world bounds if available
        if target.world and hasattr(target.world, 'width') and hasattr(target.world, 'height'):
            world_width = target.world.width
            world_height = target.world.height
            
            # Calculate max camera position (world size in pixels - screen size)
            max_camera_x = max(0, world_width * TILE_SIZE - SCREEN_WIDTH)
            max_camera_y = max(0, world_height * TILE_SIZE - SCREEN_HEIGHT)
            
            # Ensure the camera doesn't go out of bounds
            self.x = max(0, min(self.x, max_camera_x))
            self.y = max(0, min(self.y, max_camera_y))
        else:
            # Fallback to default bounds if world reference is missing
            world_width = 50
            world_height = 50
            self.x = max(0, min(self.x, world_width * TILE_SIZE - SCREEN_WIDTH))
            self.y = max(0, min(self.y, world_height * TILE_SIZE - SCREEN_HEIGHT))

class Game:
    """Main game class."""
    
    def __init__(self):
        """Initialize the game."""
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption(TITLE)
        
        # Create the screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MAIN_MENU
        
        # Game objects
        self.world = None
        self.player = None
        self.clones = []
        self.guards = []
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
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
    
    def _load_built_in_levels(self):
        """Load built-in levels from files."""
        levels_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "levels")
        
        # If directory doesn't exist, create some default level data
        if not os.path.exists(levels_dir):
            # Create a few default levels
            for i in range(1, 4):
                # Increase complexity with level number
                min_rooms = 3 + i
                max_rooms = 6 + i
                self.built_in_levels.append(self.level_generator.generate_level(min_rooms, max_rooms))
        else:
            # Load levels from files
            level_files = [f for f in os.listdir(levels_dir) if f.endswith(".txt")]
            level_files.sort()  # Sort by name so level1.txt comes before level2.txt
            
            for level_file in level_files:
                level_path = os.path.join(levels_dir, level_file)
                level_data = load_level_from_file(level_path)
                self.built_in_levels.append(level_data)
    
    def _start_game(self):
        """Start a new game."""
        try:
            self.state = STATE_PLAYING
            self.current_level = 1
            self.player_caught = False
            self.level_completed = False
            
            # Initialize the game world and entities
            success = self._load_level(self.current_level)
            
            # If level loading failed, try to generate a random level
            if not success:
                print("Using random level as fallback")
                self._generate_random_level()
        except Exception as e:
            print(f"Error starting game: {e}")
            import traceback
            traceback.print_exc()
            
            # Create a basic fallback level
            self._create_fallback_level()
    
    def _load_level(self, level_number):
        """
        Load a specific level.
        
        Args:
            level_number (int): Level number to load
        """
        try:
            # First try to load built-in level
            if level_number <= len(self.built_in_levels):
                level_data = self.built_in_levels[level_number - 1]
                self.world = World(level_data["width"], level_data["height"])
                self.world.load_from_data(level_data)
                
                # Set up player
                self.player = Player(level_data["player_start"][0], level_data["player_start"][1])
                
                # Set up guards
                self.guards = []
                for guard_data in level_data.get("guards", []):
                    guard = Guard(guard_data["position"][0], guard_data["position"][1])
                    if "patrol_route" in guard_data:
                        guard.patrol_route = guard_data["patrol_route"]
                    else:
                        # Generate a patrol route
                        guard.patrol_route = self._generate_patrol_route(
                            (guard.x, guard.y), self.world
                        )
                    self.guards.append(guard)
                
                # Reset clones
                self.clones = []
                
                # Reset camera
                self.camera.update(self.player)
                
                return True
            else:
                # Generate procedural level if no built-in level exists
                self._generate_random_level()
                return True
        except Exception as e:
            print(f"Error loading level {level_number}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_random_level(self):
        """Generate a random level using the procedural generator."""
        try:
            # Generate the level and player position
            level_data = self.level_generator.generate_level(self.current_level)
            
            # Create world from generated data
            self.world = World(level_data["width"], level_data["height"])
            self.world.load_from_data(level_data)
            
            # Set up player
            self.player = Player(level_data["player_start"][0], level_data["player_start"][1])
            
            # Set up guards
            self.guards = []
            for guard_data in level_data.get("guards", []):
                guard = Guard(guard_data["position"][0], guard_data["position"][1])
                if "patrol_route" in guard_data:
                    guard.patrol_route = guard_data["patrol_route"]
                else:
                    # Generate a patrol route
                    guard.patrol_route = self._generate_patrol_route(
                        (guard.x, guard.y), self.world
                    )
                self.guards.append(guard)
            
            # Reset clones
            self.clones = []
            
            # Reset camera
            self.camera.update(self.player)
        except Exception as e:
            print(f"Error generating random level: {e}")
            self._create_fallback_level()
    
    def _create_fallback_level(self):
        """Create a simple fallback level in case of errors."""
        # Create a small empty world
        self.world = World(20, 15)
        
        # Fill with floor tiles
        for x in range(20):
            for y in range(15):
                if x == 0 or y == 0 or x == 19 or y == 14:
                    self.world.set_tile(x, y, TILE_WALL)
                else:
                    self.world.set_tile(x, y, TILE_FLOOR)
        
        # Place exit
        self.world.set_tile(18, 13, TILE_EXIT)
        
        # Initialize player
        self.player = Player(5, 5)
        
        # Reset guards and clones
        self.guards = []
        self.clones = []
        
        # Reset camera
        self.camera.update(self.player)
    
    def _generate_patrol_route(self, start_pos, world):
        """
        Generate a patrol route for a guard.
        
        Args:
            start_pos (tuple): Starting position (x, y)
            world (World): The game world
            
        Returns:
            list: List of positions forming a patrol route
        """
        x, y = start_pos
        patrol_route = [start_pos]
        
        # Try to find walkable positions in 4 directions
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for direction in directions:
            dx, dy = direction
            path_length = 0
            current_x, current_y = x, y
            
            # Try to extend the patrol route in this direction
            for _ in range(5):  # Try up to 5 steps
                next_x, next_y = current_x + dx, current_y + dy
                if world.is_walkable(next_x, next_y):
                    current_x, current_y = next_x, next_y
                    path_length += 1
                else:
                    break
            
            # If we found a valid path, add the end point
            if path_length > 0:
                patrol_route.append((current_x, current_y))
        
        # If we don't have enough points, add the start position again
        if len(patrol_route) < 2:
            patrol_route.append(start_pos)
            
        return patrol_route
    
    def next_level(self):
        """Advance to the next level."""
        self.current_level += 1
        self.load_level(self.current_level)
        
    def restart_level(self):
        """Restart the current level."""
        self.load_level(self.current_level)
    
    def handle_events(self):
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if self.state == STATE_MAIN_MENU:
                    self._handle_main_menu_input(event.key)
                elif self.state == STATE_PLAYING:
                    self._handle_playing_input(event.key)
                elif self.state == STATE_PAUSED:
                    self._handle_paused_input(event.key)
                elif self.state == STATE_LEVEL_COMPLETE:
                    self._handle_level_complete_input(event.key)
                elif self.state == STATE_GAME_OVER:
                    self._handle_game_over_input(event.key)
                elif self.state == STATE_DIALOGUE:
                    self._handle_dialogue_input(event.key)
                elif self.state == STATE_RULES:
                    self._handle_rules_input(event.key)
    
    def _handle_main_menu_input(self, key):
        """Handle input on the main menu."""
        if key == pygame.K_RETURN:
            self._start_game()
        elif key == pygame.K_h:
            self.state = STATE_RULES
        elif key == pygame.K_q:
            self.running = False
    
    def _handle_rules_input(self, key):
        """Handle input on the rules screen."""
        if key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
            self.state = STATE_MAIN_MENU
    
    def update(self):
        """Update game state."""
        # Get delta time
        self.dt = self.clock.get_time() / 1000.0  # Convert ms to seconds
        
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
                        self.player.move(dx, dy, self.world)
                        self.last_move_time = current_time
                
                # Update clones
                for i in range(len(self.clones) - 1, -1, -1):
                    clone = self.clones[i]
                    if not clone.update(self):
                        # Remove inactive clones
                        self.clones.pop(i)
                
                # Update guards
                for guard in self.guards:
                    guard.update(self)
                    
                # Update player paw prints
                if self.player:
                    self.player.update(self)
                
                # Update camera to follow player
                if self.player:
                    self.camera.update(self.player)
                
                # Check for level completion
                if self.world and self.world.level_completed:
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
            import traceback
            traceback.print_exc()
    
    def render(self):
        """Render the game."""
        self.screen.fill(BG_COLOR)
        
        if self.state == STATE_MAIN_MENU:
            self._render_main_menu()
        elif self.state == STATE_RULES:
            self._render_rules()
        elif self.state in [STATE_PLAYING, STATE_PAUSED, STATE_TIME_TRAVEL, STATE_DIALOGUE]:
            self._render_game()
            
            if self.state == STATE_PAUSED:
                self._render_pause_menu()
            if self.state == STATE_DIALOGUE:
                self._render_dialogue_box()
        elif self.state == STATE_LEVEL_COMPLETE:
            self._render_game()
            self._render_level_complete()
        elif self.state == STATE_GAME_OVER:
            self._render_game()
            self._render_game_over()
        
        # Always render messages if there are any
        if self.message:
            self._render_message()
        
        pygame.display.flip()
    
    def _render_main_menu(self):
        """Render the main menu."""
        # Draw a fancy background with paw patterns
        for y in range(0, SCREEN_HEIGHT, 40):
            for x in range(0, SCREEN_WIDTH, 40):
                size = 36 + 4 * int(abs((time.time()*0.5) % 1.0 - 0.5) * 10)
                alpha = 20 + 10 * int(abs((time.time()*0.3 + x*0.01 + y*0.01) % 1.0 - 0.5) * 10)
                if random.random() < 0.3:
                    self._draw_decorative_paw(x + 20, y + 20, 
                                            (DOGGY_BROWN[0], DOGGY_BROWN[1], DOGGY_BROWN[2], alpha), 
                                            size // 3)
                else:
                    pygame.draw.rect(self.screen, 
                                   (DOGGY_BROWN[0], DOGGY_BROWN[1], DOGGY_BROWN[2], alpha), 
                                   (x, y, size, size), 1)
        
        # Draw a panel for the menu
        panel_width = 500
        panel_height = 400
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        
        # Panel background
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((UI_BG[0], UI_BG[1], UI_BG[2], 230))
        self.screen.blit(panel, (panel_x, panel_y))
        
        # Panel border
        pygame.draw.rect(self.screen, UI_HIGHLIGHT, 
                       (panel_x, panel_y, panel_width, panel_height), 3)
        
        # Draw doggy mascot for the menu
        mascot_size = 100
        self._draw_doggy_mascot(panel_x + panel_width // 2 - mascot_size // 2, 
                              panel_y + 40, mascot_size)
        
        # Menu options
        start_text = self.font.render("Press ENTER to Start", True, UI_TEXT)
        rules_text = self.font.render("Press H for Help & Rules", True, UI_TEXT)
        quit_text = self.font.render("Press Q to Quit", True, UI_TEXT)
        
        # Draw menu options with bone decorations
        button_y = panel_y + 180
        self._draw_menu_button(panel_x + 50, button_y, panel_width - 100, 40, 
                              start_text, DOGGY_BROWN)
        
        button_y += 60
        self._draw_menu_button(panel_x + 50, button_y, panel_width - 100, 40, 
                              rules_text, DOGGY_BROWN)
        
        button_y += 60
        self._draw_menu_button(panel_x + 50, button_y, panel_width - 100, 40, 
                              quit_text, DOGGY_BROWN)
    
    def _draw_menu_button(self, x, y, width, height, text, color):
        """Draw a menu button with bone decoration."""
        # Button background
        pygame.draw.rect(self.screen, (color[0], color[1], color[2], 180), 
                       (x, y, width, height))
        pygame.draw.rect(self.screen, UI_HIGHLIGHT, 
                       (x, y, width, height), 2)
        
        # Draw bone decorations
        bone_size = 15
        self._draw_mini_bone(x + bone_size, y + height//2, bone_size, DOGGY_BEIGE)
        self._draw_mini_bone(x + width - bone_size, y + height//2, bone_size, DOGGY_BEIGE)
        
        # Draw text
        self.screen.blit(text, (x + (width - text.get_width()) // 2, 
                              y + (height - text.get_height()) // 2))
    
    def _draw_doggy_mascot(self, x, y, size):
        """Draw a larger cute doggy mascot for the main menu."""
        # Body (sitting dog)
        body_color = DOGGY_BROWN
        
        # Draw dog body (oval)
        pygame.draw.ellipse(self.screen, body_color, 
                          (x + size//4, y + size//3, size//2, size//2))
        
        # Draw head (circle)
        head_size = size // 2
        pygame.draw.circle(self.screen, body_color, 
                         (x + size//2, y + size//3), head_size // 2)
        
        # Ears
        ear_size = head_size // 3
        pygame.draw.ellipse(self.screen, body_color, 
                          (x + size//3 - ear_size, y + size//6,
                           ear_size, ear_size*1.5))
        pygame.draw.ellipse(self.screen, body_color, 
                          (x + size//2 + size//6, y + size//6,
                           ear_size, ear_size*1.5))
        
        # Eyes
        eye_size = head_size // 8
        pygame.draw.circle(self.screen, DOGGY_BLACK, 
                         (x + size//2 - eye_size*2, y + size//3 - 2), 
                         eye_size)
        pygame.draw.circle(self.screen, DOGGY_BLACK, 
                         (x + size//2 + eye_size*2, y + size//3 - 2), 
                         eye_size)
        
        # Shine in eyes
        pygame.draw.circle(self.screen, WHITE, 
                         (x + size//2 - eye_size*2 + 2, y + size//3 - 4), 
                         eye_size//3)
        pygame.draw.circle(self.screen, WHITE, 
                         (x + size//2 + eye_size*2 + 2, y + size//3 - 4), 
                         eye_size//3)
        
        # Nose
        pygame.draw.circle(self.screen, DOGGY_BLACK, 
                         (x + size//2, y + size//3 + eye_size*2), 
                         eye_size)
        
        # Mouth
        mouth_width = head_size // 2
        pygame.draw.arc(self.screen, DOGGY_BLACK, 
                       (x + size//2 - mouth_width//2, y + size//3 + eye_size*2, 
                        mouth_width, eye_size*3), 
                        0, math.pi, 2)
        
        # Tongue (occasionally sticks out)
        if time.time() % 5 < 0.5:  # Every 5 seconds, show for 0.5 seconds
            pygame.draw.circle(self.screen, DOGGY_PINK, 
                            (x + size//2, y + size//3 + eye_size*4), 
                            eye_size*1.2)
        
        # Collar
        pygame.draw.rect(self.screen, DOGGY_BLUE, 
                       (x + size//3, y + size//2 + 4, 
                        size//3, size//20))
        
        # Tag
        pygame.draw.circle(self.screen, DOGGY_YELLOW, 
                         (x + size//2, y + size//2 + 10), 
                         size//20)
        
        # Paws
        paw_size = size // 12
        pygame.draw.ellipse(self.screen, body_color, 
                          (x + size//4, y + size//3 + size//2,
                           paw_size*2, paw_size))
        pygame.draw.ellipse(self.screen, body_color, 
                          (x + size//2 + size//8, y + size//3 + size//2,
                           paw_size*2, paw_size))
        
        # Tail (wagging animation)
        tail_angle = math.sin(time.time() * 5) * 0.5
        tail_x = x + size//2 + size//4
        tail_y = y + size//3 + size//8
        tail_length = size // 4
        end_x = tail_x + math.cos(tail_angle) * tail_length
        end_y = tail_y + math.sin(tail_angle) * tail_length
        pygame.draw.line(self.screen, body_color, 
                        (tail_x, tail_y), (end_x, end_y), 
                        size // 20)
        
        # Title with paw prints
        title_text = self.title_font.render("TEMPORAL MAZE", True, UI_TEXT)
        subtitle_text = self.font.render("A Time-Traveling Puppy Adventure", True, UI_TEXT)
        
        # Randomize paw print positions a bit
        paw_positions = []
        for i in range(5):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-5, 5)
            paw_positions.append((x - 30 + i * 30 + offset_x, y + size + 20 + offset_y))
        
        # Draw paw trail under title
        for pos in paw_positions:
            self._draw_decorative_paw(pos[0], pos[1], UI_HIGHLIGHT, 12)
        
        # Draw text centered below mascot
        self.screen.blit(title_text, 
                        (x + size//2 - title_text.get_width()//2, 
                        y + size + 40))
        self.screen.blit(subtitle_text, 
                        (x + size//2 - subtitle_text.get_width()//2, 
                        y + size + 40 + title_text.get_height() + 5))
    
    def _render_game(self):
        """Render the game world and entities."""
        try:
            # Only render if we have a world
            if not self.world:
                return
            
            # Render the world
            self.world.render(self.screen, (self.camera.x, self.camera.y))
            
            # Render paw prints for player
            if self.player and hasattr(self.player, 'paw_prints'):
                for paw in self.player.paw_prints:
                    screen_pos = self.camera.apply(type('obj', (), {'x': paw["x"], 'y': paw["y"]}))
                    frame = assets.get_animation_frame("paw_prints", paw["frame"])
                    self.screen.blit(frame, screen_pos)
            
            # Render clones and their paw prints
            for clone in self.clones:
                # Render clone's paw prints if they exist
                if hasattr(clone, 'paw_prints'):
                    for paw in clone.paw_prints:
                        screen_pos = self.camera.apply(type('obj', (), {'x': paw["x"], 'y': paw["y"]}))
                        frame = assets.get_animation_frame("paw_prints", paw["frame"])
                        # Make clone paw prints slightly different color
                        paw_frame = frame.copy()
                        paw_frame.fill((150, 150, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
                        self.screen.blit(paw_frame, screen_pos)
                
                # Only render clones that are in view
                screen_pos = self.camera.apply(clone)
                if (0 <= screen_pos[0] < SCREEN_WIDTH and 
                    0 <= screen_pos[1] < SCREEN_HEIGHT):
                    # Get clone direction safely
                    direction = getattr(clone, 'facing', 'right')
                    self.screen.blit(assets.get_image("clone", direction), screen_pos)
            
            # Render guards
            for guard in self.guards:
                screen_pos = self.camera.apply(guard)
                if (0 <= screen_pos[0] < SCREEN_WIDTH and 
                    0 <= screen_pos[1] < SCREEN_HEIGHT):
                    # Choose image based on guard state
                    if guard.state == GUARD_ALERTED:
                        image = assets.get_image("guard_alerted")
                    else:
                        image = assets.get_image("guard")
                    self.screen.blit(image, screen_pos)
            
            # Render player
            if self.player:
                player_pos = self.camera.apply(self.player)
                # Get player direction safely
                direction = getattr(self.player, 'facing', 'right')
                self.screen.blit(assets.get_image("player", direction), player_pos)
            
            # Render UI
            self._render_ui()
        except Exception as e:
            # Print error but don't crash
            print(f"Error in game rendering: {e}")
            import traceback
            traceback.print_exc()
    
    def _render_ui(self):
        """Render the game UI."""
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
        energy_text = self.font.render(f"Energy: {self.player.energy}/{self.player.energy_max}", True, UI_TEXT)
        self.screen.blit(energy_text, (info_box_width + 30, 50))
        
        # Draw energy bones (visual indicator)
        for i in range(self.player.energy_max):
            bone_x = info_box_width + 30 + i * 25
            bone_y = 75
            bone_color = DOGGY_BROWN if i < self.player.energy else DOGGY_BEIGE
            self._draw_mini_bone(bone_x, bone_y, 20, bone_color)
        
        # Clone and keys box
        self._draw_bone_box(info_box_width*2 + 30, 40, info_box_width, 80)
        
        keys_text = self.font.render(f"Keys: {self.player.keys}", True, UI_TEXT)
        self.screen.blit(keys_text, (info_box_width*2 + 40, 50))
        
        # Draw key bones
        for i in range(self.player.keys):
            key_x = info_box_width*2 + 100 + i * 20
            key_y = 55
            self._draw_mini_bone(key_x, key_y, 15, DOGGY_YELLOW)
        
        clones_text = self.font.render(f"Clones: {len(self.clones)}", True, UI_TEXT)
        self.screen.blit(clones_text, (info_box_width*2 + 40, 80))
        
        # Draw clone indicators (small pawprints)
        for i in range(len(self.clones)):
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
        """Draw a box with bone-themed border."""
        # Box background
        pygame.draw.rect(self.screen, UI_BG, (x, y, width, height))
        
        # Draw bone-themed border
        bone_size = 15
        spacing = bone_size * 2
        
        # Top border
        for bx in range(x + bone_size, x + width - bone_size, spacing):
            self._draw_mini_bone(bx, y, bone_size, UI_HIGHLIGHT)
        
        # Bottom border
        for bx in range(x + bone_size, x + width - bone_size, spacing):
            self._draw_mini_bone(bx, y + height, bone_size, UI_HIGHLIGHT)
        
        # Left border
        for by in range(y + bone_size, y + height - bone_size, spacing):
            self._draw_mini_bone(x, by, bone_size, UI_HIGHLIGHT)
        
        # Right border
        for by in range(y + bone_size, y + height - bone_size, spacing):
            self._draw_mini_bone(x + width, by, bone_size, UI_HIGHLIGHT)
        
        # Corners (paw prints)
        self._draw_decorative_paw(x, y, UI_HIGHLIGHT, bone_size)
        self._draw_decorative_paw(x + width, y, UI_HIGHLIGHT, bone_size)
        self._draw_decorative_paw(x, y + height, UI_HIGHLIGHT, bone_size)
        self._draw_decorative_paw(x + width, y + height, UI_HIGHLIGHT, bone_size)
    
    def _draw_mini_bone(self, x, y, size, color):
        """Draw a mini bone."""
        # Draw the middle rectangle 
        rect_width = size // 2
        rect_height = size // 4
        rect_x = x - rect_width // 2
        rect_y = y - rect_height // 2
        pygame.draw.rect(self.screen, color, (rect_x, rect_y, rect_width, rect_height))
        
        # Draw the circular ends
        radius = size // 6
        pygame.draw.circle(self.screen, color, (rect_x, rect_y + rect_height // 2), radius)
        pygame.draw.circle(self.screen, color, (rect_x + rect_width, rect_y + rect_height // 2), radius)
    
    def _draw_decorative_paw(self, x, y, color, size):
        """Draw a decorative paw print."""
        # Main pad
        pygame.draw.ellipse(self.screen, color, 
                          (x - size // 2, y - size // 2, 
                           size, size))
        
        # Toe pads - small circles above the main pad
        toe_size = size // 3
        for i in range(3):
            toe_x = x - size // 2 + (i * toe_size)
            toe_y = y - size // 2 - toe_size // 2
            pygame.draw.circle(self.screen, color, (toe_x, toe_y), toe_size // 2)
    
    def _draw_doggy_logo(self, x, y, size):
        """Draw a cute doggy logo."""
        # Draw doggy head
        pygame.draw.circle(self.screen, DOGGY_BROWN, (x + size, y + size), size)
        
        # Ears
        ear_size = size // 3
        pygame.draw.ellipse(self.screen, DOGGY_BROWN, 
                          (x + size // 2, y + size // 4,
                           ear_size * 2, ear_size))
        pygame.draw.ellipse(self.screen, DOGGY_BROWN, 
                          (x + size + size // 2, y + size // 4,
                           ear_size * 2, ear_size))
        
        # Eyes
        eye_size = size // 5
        pygame.draw.circle(self.screen, DOGGY_BLACK, 
                         (x + size - eye_size, y + size - 2), 
                         eye_size // 2)
        pygame.draw.circle(self.screen, DOGGY_BLACK, 
                         (x + size + eye_size, y + size - 2), 
                         eye_size // 2)
        
        # Nose
        pygame.draw.circle(self.screen, DOGGY_BLACK, 
                         (x + size, y + size + 5), 
                         eye_size // 2)
        
        # Mouth
        pygame.draw.arc(self.screen, DOGGY_BLACK, 
                       (x + size - eye_size, y + size + 5, 
                        eye_size * 2, eye_size), 
                        0, math.pi, 1)
        
        # Draw text
        title_text = self.font.render("TEMPORAL MAZE", True, UI_TEXT)
        self.screen.blit(title_text, (x + size*2 + 10, y + size - title_text.get_height()//2))
    
    def _render_pause_menu(self):
        """Render the pause menu overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((LAVENDER[0], LAVENDER[1], LAVENDER[2], 180))
        self.screen.blit(overlay, (0, 0))
        
        # Pause menu text
        pause_text = self.title_font.render("PAUSED", True, DARK_BLUE)
        resume_text = self.font.render("Press ESC to Resume", True, BLUE)
        rules_text = self.font.render("Press H for Help & Rules", True, BLUE)
        quit_text = self.font.render("Press Q to Return to Main Menu", True, BLUE)
        
        # Center the text
        pause_x = (SCREEN_WIDTH - pause_text.get_width()) // 2
        pause_y = SCREEN_HEIGHT // 3
        
        resume_x = (SCREEN_WIDTH - resume_text.get_width()) // 2
        resume_y = pause_y + pause_text.get_height() + 30
        
        rules_x = (SCREEN_WIDTH - rules_text.get_width()) // 2
        rules_y = resume_y + resume_text.get_height() + 20
        
        quit_x = (SCREEN_WIDTH - quit_text.get_width()) // 2
        quit_y = rules_y + rules_text.get_height() + 20
        
        # Draw the text
        self.screen.blit(pause_text, (pause_x, pause_y))
        self.screen.blit(resume_text, (resume_x, resume_y))
        self.screen.blit(rules_text, (rules_x, rules_y))
        self.screen.blit(quit_text, (quit_x, quit_y))
    
    def _render_dialogue_box(self):
        """Render a dialogue box for terminal messages."""
        # Semi-transparent overlay for the bottom third of the screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 3), pygame.SRCALPHA)
        overlay.fill(UI_BG)
        self.screen.blit(overlay, (0, SCREEN_HEIGHT - SCREEN_HEIGHT // 3))
        
        # Draw a border with nice styling
        box_rect = (10, SCREEN_HEIGHT - SCREEN_HEIGHT // 3 + 10, 
                  SCREEN_WIDTH - 20, SCREEN_HEIGHT // 3 - 20)
        pygame.draw.rect(self.screen, UI_HIGHLIGHT, box_rect, 3)
        
        # Add a title bar
        title_rect = (box_rect[0], box_rect[1], box_rect[2], 30)
        pygame.draw.rect(self.screen, UI_HIGHLIGHT, title_rect)
        terminal_title = self.font.render("TERMINAL MESSAGE", True, WHITE)
        self.screen.blit(terminal_title, 
                       (box_rect[0] + (box_rect[2] - terminal_title.get_width()) // 2, 
                        box_rect[1] + 5))
        
        # Render the message with word wrapping
        if self.message:
            words = self.message.split(' ')
            lines = []
            line = ""
            
            for word in words:
                test_line = line + word + " "
                # Check if the line is too long
                if self.font.size(test_line)[0] > SCREEN_WIDTH - 40:
                    lines.append(line)
                    line = word + " "
                else:
                    line = test_line
            
            # Add the last line
            if line:
                lines.append(line)
            
            # Render each line
            for i, line in enumerate(lines):
                text = self.font.render(line, True, UI_TEXT)
                self.screen.blit(text, (20, SCREEN_HEIGHT - SCREEN_HEIGHT // 3 + 50 + i * 30))
            
            # Continue prompt with pulsing effect
            alpha = 128 + int(127 * abs(math.sin(time.time() * 3)))
            continue_text = self.font.render("Press ENTER or SPACE to continue", True, UI_TEXT)
            continue_x = (SCREEN_WIDTH - continue_text.get_width()) // 2
            continue_y = SCREEN_HEIGHT - 40
            self.screen.blit(continue_text, (continue_x, continue_y))
    
    def _render_level_complete(self):
        """Render the level complete overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((MINT[0], MINT[1], MINT[2], 180))
        self.screen.blit(overlay, (0, 0))
        
        # Level complete text
        complete_text = self.title_font.render("LEVEL COMPLETE!", True, DARK_BLUE)
        continue_text = self.font.render("Press ENTER to continue", True, BLUE)
        
        # Center the text
        complete_x = (SCREEN_WIDTH - complete_text.get_width()) // 2
        complete_y = SCREEN_HEIGHT // 3
        
        continue_x = (SCREEN_WIDTH - continue_text.get_width()) // 2
        continue_y = complete_y + complete_text.get_height() + 30
        
        # Draw the text
        self.screen.blit(complete_text, (complete_x, complete_y))
        self.screen.blit(continue_text, (continue_x, continue_y))
    
    def _render_game_over(self):
        """Render the game over overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((RED[0], RED[1], RED[2], 160))
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        over_text = self.title_font.render("GAME OVER", True, WHITE)
        restart_text = self.font.render("Press ENTER to Restart Level", True, WHITE)
        quit_text = self.font.render("Press Q to Return to Main Menu", True, WHITE)
        
        # Center the text
        over_x = (SCREEN_WIDTH - over_text.get_width()) // 2
        over_y = SCREEN_HEIGHT // 3
        
        restart_x = (SCREEN_WIDTH - restart_text.get_width()) // 2
        restart_y = over_y + over_text.get_height() + 30
        
        quit_x = (SCREEN_WIDTH - quit_text.get_width()) // 2
        quit_y = restart_y + restart_text.get_height() + 20
        
        # Draw the text
        self.screen.blit(over_text, (over_x, over_y))
        self.screen.blit(restart_text, (restart_x, restart_y))
        self.screen.blit(quit_text, (quit_x, quit_y))
    
    def _render_message(self):
        """Render a temporary message."""
        if not self.message:
            return
            
        # Create a semi-transparent background
        message_surf = self.font.render(self.message, True, WHITE)
        bg_width = message_surf.get_width() + 20
        bg_height = message_surf.get_height() + 10
        
        # Position at the bottom center of the screen
        bg_x = (SCREEN_WIDTH - bg_width) // 2
        bg_y = SCREEN_HEIGHT - bg_height - 40
        
        # Draw the background and text
        pygame.draw.rect(self.screen, (0, 0, 0, 128), 
                        (bg_x, bg_y, bg_width, bg_height))
        pygame.draw.rect(self.screen, WHITE, 
                        (bg_x, bg_y, bg_width, bg_height), 1)
        
        self.screen.blit(message_surf, (bg_x + 10, bg_y + 5))
    
    def show_message(self, message, duration=2.0):
        """
        Show a message for a specified duration.
        
        Args:
            message (str): Message to display
            duration (float): Duration in seconds (0 for persistent)
        """
        self.message = message
        self.message_timer = duration
    
    def _render_rules(self):
        """Render the game rules screen."""
        # Background
        self.screen.fill(BG_COLOR)
        
        # Title
        title = self.title_font.render("GAME RULES", True, DARK_BLUE)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        title_y = 40
        self.screen.blit(title, (title_x, title_y))
        
        # Rules content
        rules = [
            "OBJECTIVE:",
            "Navigate through time-bending mazes to reach the exit portal in each level.",
            "",
            "GAMEPLAY:",
            "1. Move through the maze using WASD or Arrow Keys.",
            "2. Avoid guards - they will capture you if they see you!",
            "3. Collect keys to unlock doors.",
            "4. Find and use terminals for useful information.",
            "5. Energy potions restore your time travel energy.",
            "",
            "TIME TRAVEL MECHANICS:",
            "1. Press T to create a time clone of yourself.",
            "2. Your clone will repeat your past movements exactly.",
            "3. Use clones to trigger multiple switches simultaneously.",
            "4. You can have up to 3 clones active at once.",
            "5. Each clone costs energy to create.",
            "",
            "SPECIAL ELEMENTS:",
            "- Switches: Trigger and hold down to open linked doors.",
            "- Doors: Opened by switches or keys.",
            "- Portals: Teleport you to a linked location.",
            "- Terminals: Provide story elements and hints.",
            "",
            "CONTROLS:",
            "- WASD/Arrow Keys: Move",
            "- T: Create time clone",
            "- R: Restart level",
            "- ESC: Pause game",
            "- H: View this help screen"
        ]
        
        # Render each line
        y_pos = title_y + 80
        for line in rules:
            if line == "":
                y_pos += 15  # Extra space for breaks
                continue
            
            if ":" in line and line.endswith(":"):
                # Section headers
                text = self.font.render(line, True, BLUE)
                text_x = 100
            else:
                # Normal text
                text = self.font.render(line, True, DARK_BLUE)
                text_x = 120
            
            self.screen.blit(text, (text_x, y_pos))
            y_pos += 25
        
        # Return to menu instruction
        back_text = self.font.render("Press ESC or BACKSPACE to return to menu", True, BLUE)
        back_x = (SCREEN_WIDTH - back_text.get_width()) // 2
        back_y = SCREEN_HEIGHT - 40
        self.screen.blit(back_text, (back_x, back_y))
    
    def _handle_playing_input(self, key):
        """Handle input during gameplay."""
        if key == pygame.K_ESCAPE:
            self.state = STATE_PAUSED
        elif key == pygame.K_r:
            self.restart_level()
        elif key == pygame.K_t:
            # Initiate time travel if the player has energy
            if self.player.energy > 0:
                self.state = STATE_TIME_TRAVEL
                self.time_travel_steps = 0
                self.show_message("Time Travel: Enter number of steps back (1-9)", 0)
            else:
                self.show_message("Not enough time energy!", 2.0)
        elif key == pygame.K_h:
            self.state = STATE_RULES

    def _handle_paused_input(self, key):
        """Handle input when game is paused."""
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYING
        elif key == pygame.K_q:
            self.state = STATE_MAIN_MENU
        elif key == pygame.K_h:
            self.state = STATE_RULES

    def _handle_level_complete_input(self, key):
        """Handle input when a level is completed."""
        if key == pygame.K_RETURN:
            print(f"Transitioning from level {self.current_level} to next level")
            self.current_level += 1
            
            # Clear previous level data
            self.clones = []
            self.guards = []
            self.player = None
            self.world = None
            self.level_completed = False
            
            # Load the next level
            success = self._load_level(self.current_level)
            
            # Switch back to playing state
            self.state = STATE_PLAYING
            
            # If level loading failed, restart with first level
            if not success:
                print("Failed to load next level, restarting from level 1")
                self.current_level = 1
                self._load_level(self.current_level)

    def _handle_game_over_input(self, key):
        """Handle input when game is over."""
        if key == pygame.K_RETURN:
            self.restart_level()
        elif key == pygame.K_q:
            self.state = STATE_MAIN_MENU

    def _handle_dialogue_input(self, key):
        """Handle input during dialogue."""
        if key == pygame.K_RETURN or key == pygame.K_SPACE:
            self.state = STATE_PLAYING
            self.message = None
    
    def run(self):
        """Main game loop."""
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.render()
            
        pygame.quit() 