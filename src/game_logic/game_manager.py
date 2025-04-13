import os
import pygame
from .world import World
from .player import Player
from .time_travel import TimeManager

class GameManager:
    """Manages overall game state, UI, and level progression."""
    
    # Game states
    STATE_MENU = 0          # Main menu
    STATE_PLAYING = 1       # Actively playing a level
    STATE_TIME_TRAVEL = 2   # Selecting time travel amount
    STATE_LEVEL_COMPLETE = 3 # Level completed
    STATE_GAME_OVER = 4     # Game completed
    STATE_TUTORIAL = 5      # Tutorial mode
    
    # Tutorial steps
    TUTORIAL_MOVE = 0       # Movement basics
    TUTORIAL_SWITCH = 1     # Switches and doors
    TUTORIAL_TIME = 2       # Time travel
    TUTORIAL_MULTI = 3      # Multiple clones
    TUTORIAL_COMPLETE = 4   # Tutorial complete
    
    # UI Colors
    COLOR_BG = (30, 30, 50)
    COLOR_TEXT = (255, 255, 255)
    COLOR_HIGHLIGHT = (255, 255, 0)
    COLOR_BUTTON = (100, 100, 150)
    COLOR_BUTTON_HOVER = (150, 150, 200)
    COLOR_PANEL = (50, 50, 70, 200)  # with alpha
    
    def __init__(self, screen_width, screen_height):
        """
        Initialize the game manager.
        
        Args:
            screen_width (int): Width of the screen
            screen_height (int): Height of the screen
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = self.STATE_MENU
        self.current_level = 1
        self.max_level = 3  # Adjust based on your level count
        
        # Game objects
        self.world = None
        self.player = None
        self.time_manager = None
        
        # Camera position for scrolling
        self.camera_x = 0
        self.camera_y = 0
        
        # UI elements
        self.fonts = {}
        self.buttons = {}
        self.init_ui()
        
        # Tutorial state
        self.tutorial_step = self.TUTORIAL_MOVE
        self.tutorial_messages = {
            self.TUTORIAL_MOVE: [
                "Welcome to Temporal Maze!",
                "Use the ARROW KEYS or WASD to move.",
                "Try moving around to get familiar with the controls."
            ],
            self.TUTORIAL_SWITCH: [
                "Yellow tiles are SWITCHES. They control DOORS.",
                "Step on a switch to open its connected door.",
                "When you step off, the door will close again."
            ],
            self.TUTORIAL_TIME: [
                "This is where it gets interesting!",
                "Press T to create a TIME CLONE.",
                "Your clone will repeat your past movements.",
                "Use this to keep switches pressed while you move through doors."
            ],
            self.TUTORIAL_MULTI: [
                "You can create up to 3 clones at once.",
                "Each clone will follow the exact path you took.",
                "Try creating multiple clones to solve more complex puzzles."
            ],
            self.TUTORIAL_COMPLETE: [
                "Great job! You've completed the tutorial.",
                "Now you're ready for the real challenges ahead.",
                "Press SPACE to continue to the next level."
            ]
        }
        
        # Time travel state
        self.time_travel_steps = 0
        self.time_travel_max = 50
        self.time_travel_input = ""
        
        # Load the first level
        self.load_level(self.current_level)
    
    def init_ui(self):
        """Initialize UI elements including fonts and buttons."""
        # Initialize fonts
        pygame.font.init()
        self.fonts = {
            'small': pygame.font.SysFont('Arial', 16),
            'medium': pygame.font.SysFont('Arial', 24),
            'large': pygame.font.SysFont('Arial', 36),
            'title': pygame.font.SysFont('Arial', 48, bold=True)
        }
        
        # Create buttons
        button_width = 200
        button_height = 50
        button_x = self.screen_width // 2 - button_width // 2
        
        self.buttons = {
            'start': {
                'rect': pygame.Rect(button_x, 250, button_width, button_height),
                'text': 'Start Game',
                'action': self.start_game
            },
            'tutorial': {
                'rect': pygame.Rect(button_x, 320, button_width, button_height),
                'text': 'Tutorial',
                'action': self.start_tutorial
            },
            'quit': {
                'rect': pygame.Rect(button_x, 390, button_width, button_height),
                'text': 'Quit',
                'action': self.quit_game
            },
            'next_level': {
                'rect': pygame.Rect(button_x, 350, button_width, button_height),
                'text': 'Next Level',
                'action': self.next_level
            },
            'menu': {
                'rect': pygame.Rect(button_x, 420, button_width, button_height),
                'text': 'Main Menu',
                'action': self.go_to_menu
            }
        }
    
    def load_level(self, level_number):
        """
        Load a level by number.
        
        Args:
            level_number (int): Level number to load
        """
        # Build the path to the level file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        level_path = os.path.join(base_dir, f"maps/level{level_number}.txt")
        
        try:
            # Create the world
            self.world = World(level_path)
            
            # Create the player at the start position
            player_x, player_y = self.world.get_player_start_pos()
            self.player = Player(player_x, player_y)
            
            # Create the time manager
            self.time_manager = TimeManager()
            
            # Center the camera on the player
            self.camera_x = player_x
            self.camera_y = player_y
            
            # Reset any game state
            self.state = self.STATE_PLAYING
            if level_number == 1:
                self.state = self.STATE_TUTORIAL
                self.tutorial_step = self.TUTORIAL_MOVE
            
            return True
        except Exception as e:
            print(f"Error loading level {level_number}: {e}")
            return False
    
    def start_game(self):
        """Start a new game from level 1."""
        self.current_level = 1
        self.load_level(self.current_level)
        self.state = self.STATE_PLAYING
    
    def start_tutorial(self):
        """Start the tutorial (level 1)."""
        self.current_level = 1
        self.load_level(self.current_level)
        self.state = self.STATE_TUTORIAL
        self.tutorial_step = self.TUTORIAL_MOVE
    
    def next_level(self):
        """Advance to the next level."""
        self.current_level += 1
        if self.current_level > self.max_level:
            self.state = self.STATE_GAME_OVER
        else:
            self.load_level(self.current_level)
    
    def go_to_menu(self):
        """Return to the main menu."""
        self.state = self.STATE_MENU
    
    def quit_game(self):
        """Exit the game."""
        pygame.quit()
        import sys
        sys.exit()
    
    def handle_events(self):
        """
        Handle Pygame events.
        
        Returns:
            bool: False if the game should exit, True otherwise
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos)
            
            # Handle keyboard events
            if event.type == pygame.KEYDOWN:
                if self.state == self.STATE_PLAYING or self.state == self.STATE_TUTORIAL:
                    self.handle_gameplay_key(event.key)
                elif self.state == self.STATE_TIME_TRAVEL:
                    self.handle_time_travel_key(event.key)
                elif self.state == self.STATE_LEVEL_COMPLETE:
                    if event.key == pygame.K_SPACE:
                        self.next_level()
                elif self.state == self.STATE_GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.go_to_menu()
        
        return True
    
    def handle_mouse_click(self, pos):
        """
        Handle mouse click events.
        
        Args:
            pos (tuple): Mouse position (x, y)
        """
        # Check if any button was clicked
        if self.state == self.STATE_MENU:
            for button_name, button in self.buttons.items():
                if button['rect'].collidepoint(pos):
                    button['action']()
                    break
        elif self.state == self.STATE_LEVEL_COMPLETE:
            if self.buttons['next_level']['rect'].collidepoint(pos):
                self.next_level()
            elif self.buttons['menu']['rect'].collidepoint(pos):
                self.go_to_menu()
        elif self.state == self.STATE_GAME_OVER:
            if self.buttons['menu']['rect'].collidepoint(pos):
                self.go_to_menu()
    
    def handle_gameplay_key(self, key):
        """
        Handle keyboard input during gameplay.
        
        Args:
            key (int): Pygame key code
        """
        # Movement keys
        if key in [pygame.K_w, pygame.K_UP]:
            self.player.move(0, -1, self.world)
        elif key in [pygame.K_s, pygame.K_DOWN]:
            self.player.move(0, 1, self.world)
        elif key in [pygame.K_a, pygame.K_LEFT]:
            self.player.move(-1, 0, self.world)
        elif key in [pygame.K_d, pygame.K_RIGHT]:
            self.player.move(1, 0, self.world)
        
        # Time travel key
        elif key == pygame.K_t and self.player.can_use_time_travel():
            self.state = self.STATE_TIME_TRAVEL
            self.time_travel_input = ""
        
        # Reset level
        elif key == pygame.K_r:
            self.load_level(self.current_level)
        
        # Check if player is at exit
        player_x, player_y = self.player.get_position()
        if self.world.is_exit(player_x, player_y):
            if self.state == self.STATE_TUTORIAL:
                self.tutorial_step += 1
                if self.tutorial_step >= self.TUTORIAL_COMPLETE:
                    self.state = self.STATE_LEVEL_COMPLETE
            else:
                self.state = self.STATE_LEVEL_COMPLETE
        
        # Check for tutorial progression
        if self.state == self.STATE_TUTORIAL:
            # Check for specific tutorial triggers
            if self.tutorial_step == self.TUTORIAL_MOVE:
                # Check if player has moved enough to progress
                if len(self.player.history) >= 5:
                    self.tutorial_step = self.TUTORIAL_SWITCH
            elif self.tutorial_step == self.TUTORIAL_SWITCH:
                # Check if player has used a switch
                for door_pos, is_open in self.world.doors.items():
                    if is_open:
                        self.tutorial_step = self.TUTORIAL_TIME
                        break
            elif self.tutorial_step == self.TUTORIAL_TIME:
                # Check if player has created a clone
                if self.time_manager.get_active_clone_count() > 0:
                    self.tutorial_step = self.TUTORIAL_MULTI
        
        # Update camera to follow player
        self.camera_x, self.camera_y = self.player.get_position()
    
    def handle_time_travel_key(self, key):
        """
        Handle keyboard input during time travel selection.
        
        Args:
            key (int): Pygame key code
        """
        if key == pygame.K_ESCAPE:
            # Cancel time travel
            self.state = self.STATE_PLAYING
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            # Confirm time travel
            try:
                steps = int(self.time_travel_input)
                if 1 <= steps <= min(self.time_travel_max, len(self.player.history)):
                    self.time_manager.create_clone(self.player, steps)
                    self.state = self.STATE_PLAYING
                    
                    # Progress tutorial if needed
                    if self.state == self.STATE_TUTORIAL and self.tutorial_step == self.TUTORIAL_TIME:
                        self.tutorial_step = self.TUTORIAL_MULTI
            except ValueError:
                pass  # Invalid input, do nothing
            self.time_travel_input = ""
        elif key == pygame.K_BACKSPACE:
            # Delete last character
            self.time_travel_input = self.time_travel_input[:-1]
        elif pygame.K_0 <= key <= pygame.K_9 or pygame.K_KP0 <= key <= pygame.K_KP9:
            # Add digit
            if len(self.time_travel_input) < 2:  # Limit to 2 digits
                if pygame.K_0 <= key <= pygame.K_9:
                    self.time_travel_input += chr(key)
                else:
                    # Convert keypad digit to regular digit
                    self.time_travel_input += str(key - pygame.K_KP0)
    
    def update(self):
        """Update game state."""
        if self.state == self.STATE_PLAYING or self.state == self.STATE_TUTORIAL:
            # Update time clones
            self.time_manager.update_clones(self.world)
            
            # Check win condition again (in case a clone triggered it)
            player_x, player_y = self.player.get_position()
            if self.world.is_exit(player_x, player_y):
                if self.state == self.STATE_TUTORIAL:
                    self.tutorial_step += 1
                    if self.tutorial_step >= self.TUTORIAL_COMPLETE:
                        self.state = self.STATE_LEVEL_COMPLETE
                else:
                    self.state = self.STATE_LEVEL_COMPLETE
    
    def render(self, screen):
        """
        Render the game.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Clear the screen
        screen.fill(self.COLOR_BG)
        
        if self.state == self.STATE_MENU:
            self.render_menu(screen)
        elif self.state in [self.STATE_PLAYING, self.STATE_TUTORIAL, self.STATE_TIME_TRAVEL]:
            self.render_game(screen)
            
            if self.state == self.STATE_TUTORIAL:
                self.render_tutorial(screen)
            elif self.state == self.STATE_TIME_TRAVEL:
                self.render_time_travel(screen)
        elif self.state == self.STATE_LEVEL_COMPLETE:
            self.render_level_complete(screen)
        elif self.state == self.STATE_GAME_OVER:
            self.render_game_over(screen)
    
    def render_menu(self, screen):
        """
        Render the main menu.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Render title
        title = self.fonts['title'].render("Temporal Maze", True, self.COLOR_HIGHLIGHT)
        title_rect = title.get_rect(center=(self.screen_width // 2, 120))
        screen.blit(title, title_rect)
        
        # Render subtitle
        subtitle = self.fonts['medium'].render("A puzzle game with time clones", True, self.COLOR_TEXT)
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 180))
        screen.blit(subtitle, subtitle_rect)
        
        # Render buttons
        for button_name, button in self.buttons.items():
            if button_name in ['start', 'tutorial', 'quit']:
                # Check if mouse is hovering
                mouse_pos = pygame.mouse.get_pos()
                if button['rect'].collidepoint(mouse_pos):
                    color = self.COLOR_BUTTON_HOVER
                else:
                    color = self.COLOR_BUTTON
                
                # Draw button
                pygame.draw.rect(screen, color, button['rect'], border_radius=10)
                pygame.draw.rect(screen, self.COLOR_TEXT, button['rect'], 2, border_radius=10)
                
                # Draw text
                text = self.fonts['medium'].render(button['text'], True, self.COLOR_TEXT)
                text_rect = text.get_rect(center=button['rect'].center)
                screen.blit(text, text_rect)
    
    def render_game(self, screen):
        """
        Render the game world, player, and clones.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Render the world
        self.world.render(screen, self.camera_x, self.camera_y)
        
        # Render time clones
        self.time_manager.render_clones(screen, self.camera_x, self.camera_y)
        
        # Render the player
        self.player.render(screen, self.camera_x, self.camera_y)
        
        # Render UI overlay
        self.render_ui_overlay(screen)
    
    def render_ui_overlay(self, screen):
        """
        Render the UI overlay with game info.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Create a semi-transparent overlay panel
        panel_height = 60
        panel_surface = pygame.Surface((self.screen_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.COLOR_PANEL)
        screen.blit(panel_surface, (0, 0))
        
        # Level info
        level_text = self.fonts['medium'].render(f"Level: {self.current_level}", True, self.COLOR_TEXT)
        screen.blit(level_text, (20, 15))
        
        # Clone info
        clone_text = self.fonts['medium'].render(f"Clones: {self.time_manager.get_active_clone_count()}/{self.time_manager.MAX_CLONES}", True, self.COLOR_TEXT)
        clone_rect = clone_text.get_rect(midtop=(self.screen_width // 2, 15))
        screen.blit(clone_text, clone_rect)
        
        # Controls
        if self.state == self.STATE_PLAYING or self.state == self.STATE_TUTORIAL:
            controls_text = self.fonts['small'].render("ARROWS/WASD: Move | T: Time Travel | R: Reset Level | ESC: Menu", True, self.COLOR_TEXT)
            controls_rect = controls_text.get_rect(right=self.screen_width - 20, centery=30)
            screen.blit(controls_text, controls_rect)
    
    def render_tutorial(self, screen):
        """
        Render tutorial messages.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Create a semi-transparent message panel at the bottom
        panel_height = 100
        panel_surface = pygame.Surface((self.screen_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 200))  # Black with alpha
        screen.blit(panel_surface, (0, self.screen_height - panel_height))
        
        # Render tutorial messages
        if self.tutorial_step in self.tutorial_messages:
            messages = self.tutorial_messages[self.tutorial_step]
            for i, message in enumerate(messages):
                text = self.fonts['medium'].render(message, True, self.COLOR_TEXT)
                text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height - panel_height + 25 + i * 25))
                screen.blit(text, text_rect)
    
    def render_time_travel(self, screen):
        """
        Render time travel selection UI.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Black with alpha
        screen.blit(overlay, (0, 0))
        
        # Create input panel
        panel_width = 400
        panel_height = 200
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2
        
        pygame.draw.rect(overlay, (50, 50, 70), (panel_x, panel_y, panel_width, panel_height), border_radius=15)
        pygame.draw.rect(overlay, self.COLOR_TEXT, (panel_x, panel_y, panel_width, panel_height), 2, border_radius=15)
        
        # Title
        title = self.fonts['large'].render("Time Travel", True, self.COLOR_HIGHLIGHT)
        title_rect = title.get_rect(center=(self.screen_width // 2, panel_y + 40))
        screen.blit(title, title_rect)
        
        # Instructions
        instr = self.fonts['medium'].render(f"Enter steps back (1-{min(self.time_travel_max, len(self.player.history))})", True, self.COLOR_TEXT)
        instr_rect = instr.get_rect(center=(self.screen_width // 2, panel_y + 80))
        screen.blit(instr, instr_rect)
        
        # Input box
        input_box = pygame.Rect(panel_x + 100, panel_y + 110, panel_width - 200, 40)
        pygame.draw.rect(screen, self.COLOR_TEXT, input_box, 2)
        
        # Input text
        if self.time_travel_input:
            input_text = self.fonts['large'].render(self.time_travel_input, True, self.COLOR_TEXT)
            input_text_rect = input_text.get_rect(center=input_box.center)
            screen.blit(input_text, input_text_rect)
        
        # Controls
        controls = self.fonts['small'].render("Enter: Confirm | Esc: Cancel", True, self.COLOR_TEXT)
        controls_rect = controls.get_rect(center=(self.screen_width // 2, panel_y + 170))
        screen.blit(controls, controls_rect)
    
    def render_level_complete(self, screen):
        """
        Render level complete screen.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with alpha
        screen.blit(overlay, (0, 0))
        
        # Level complete message
        if self.current_level < self.max_level:
            title = self.fonts['large'].render(f"Level {self.current_level} Complete!", True, self.COLOR_HIGHLIGHT)
        else:
            title = self.fonts['large'].render("Final Level Complete!", True, self.COLOR_HIGHLIGHT)
        
        title_rect = title.get_rect(center=(self.screen_width // 2, 200))
        screen.blit(title, title_rect)
        
        # Render buttons
        button_names = ['next_level', 'menu'] if self.current_level < self.max_level else ['menu']
        for button_name in button_names:
            button = self.buttons[button_name]
            
            # Check if mouse is hovering
            mouse_pos = pygame.mouse.get_pos()
            if button['rect'].collidepoint(mouse_pos):
                color = self.COLOR_BUTTON_HOVER
            else:
                color = self.COLOR_BUTTON
            
            # Draw button
            pygame.draw.rect(screen, color, button['rect'], border_radius=10)
            pygame.draw.rect(screen, self.COLOR_TEXT, button['rect'], 2, border_radius=10)
            
            # Draw text
            text = self.fonts['medium'].render(button['text'], True, self.COLOR_TEXT)
            text_rect = text.get_rect(center=button['rect'].center)
            screen.blit(text, text_rect)
    
    def render_game_over(self, screen):
        """
        Render game over screen.
        
        Args:
            screen (pygame.Surface): The screen to render on
        """
        # Create a dark overlay
        screen.fill((20, 20, 40))
        
        # Game complete message
        title = self.fonts['large'].render("Congratulations!", True, self.COLOR_HIGHLIGHT)
        title_rect = title.get_rect(center=(self.screen_width // 2, 180))
        screen.blit(title, title_rect)
        
        subtitle = self.fonts['medium'].render("You've completed all levels!", True, self.COLOR_TEXT)
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 240))
        screen.blit(subtitle, subtitle_rect)
        
        # Message
        message = self.fonts['medium'].render("You've mastered the art of time travel.", True, self.COLOR_TEXT)
        message_rect = message.get_rect(center=(self.screen_width // 2, 280))
        screen.blit(message, message_rect)
        
        # Render menu button
        button = self.buttons['menu']
        
        # Check if mouse is hovering
        mouse_pos = pygame.mouse.get_pos()
        if button['rect'].collidepoint(mouse_pos):
            color = self.COLOR_BUTTON_HOVER
        else:
            color = self.COLOR_BUTTON
        
        # Draw button
        pygame.draw.rect(screen, color, button['rect'], border_radius=10)
        pygame.draw.rect(screen, self.COLOR_TEXT, button['rect'], 2, border_radius=10)
        
        # Draw text
        text = self.fonts['medium'].render(button['text'], True, self.COLOR_TEXT)
        text_rect = text.get_rect(center=button['rect'].center)
        screen.blit(text, text_rect) 