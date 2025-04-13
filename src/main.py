import pygame
import sys
import os

# Add absolute path to src directory to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game_logic.game_manager import GameManager

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WINDOW_TITLE = "Temporal Maze"
FPS = 60

def main():
    """Main game function."""
    pygame.init()

    # Initialize screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # Create game manager
    game_manager = GameManager(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Main game loop
    running = True
    while running:
        # Handle events
        running = game_manager.handle_events()
        
        # Update game state
        game_manager.update()
        
        # Render the game
        game_manager.render(screen)
        
        # Flip the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 