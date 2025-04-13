"""
Asset manager for the Temporal Maze game.
Handles loading and storing game assets like images and sounds.
"""

import os
import pygame
import math
import random
from .constants import *

# Ensure pygame is initialized for asset loading
pygame.init()

class AssetManager:
    def __init__(self):
        """Initialize the asset manager."""
        self.images = {}
        self.sounds = {}
        self.fonts = {}
        self.animations = {}
        self.create_default_assets()
        
    def create_default_assets(self):
        """
        Create default pixel art assets using pygame drawing functions.
        This ensures the game has visuals even without external image files.
        """
        # Create pixel art surfaces for each game element with doggy theme
        self._create_default_tile(TILE_WALL, DOGGY_DARK_BROWN, "wall")
        self._create_default_tile(TILE_FLOOR, DOGGY_BEIGE, "floor")
        self._create_default_tile(TILE_SWITCH, DOGGY_YELLOW, "switch") 
        self._create_default_tile(TILE_DOOR_CLOSED, DOGGY_PINK, "door_closed")
        self._create_default_tile(TILE_DOOR_OPEN, DOGGY_GREEN, "door_open")
        self._create_default_tile(TILE_EXIT, DOGGY_BLUE, "exit")
        self._create_default_tile(TILE_PORTAL_A, DOGGY_BLUE, "portal_a")
        self._create_default_tile(TILE_PORTAL_B, DOGGY_BLUE, "portal_b")
        self._create_default_tile(TILE_ITEM_KEY, DOGGY_YELLOW, "key")
        self._create_default_tile(TILE_ITEM_POTION, DOGGY_GREEN, "potion")
        self._create_default_tile(TILE_TERMINAL, DOGGY_BLUE, "terminal")
        
        # Create player sprite (doggy style)
        self._create_player_sprite()
        
        # Create clone sprite (transparent doggy)
        self._create_clone_sprite()
        
        # Create guard sprite (antagonist doggy)
        self._create_guard_sprite()
        
        # Create paw prints
        self._create_paw_prints()
        
        # Create fonts
        self.fonts["small"] = pygame.font.SysFont("Comic Sans MS", FONT_SMALL)
        self.fonts["medium"] = pygame.font.SysFont("Comic Sans MS", FONT_MEDIUM)
        self.fonts["large"] = pygame.font.SysFont("Comic Sans MS", FONT_LARGE)
        self.fonts["title"] = pygame.font.SysFont("Comic Sans MS", FONT_TITLE, bold=True)
        
    def _create_default_tile(self, tile_type, color, name):
        """Create a default pixel art tile with cute doggy theme."""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill(color)
        
        # Add patterns/details to distinguish tiles
        if tile_type == TILE_WALL:
            # Add bone pattern to walls
            for i in range(0, TILE_SIZE, 16):
                for j in range(0, TILE_SIZE, 16):
                    self._draw_mini_bone(surface, j + 4, i + 4, 8, DOGGY_BEIGE)
        
        elif tile_type == TILE_FLOOR:
            # Add subtle paw print to some floor tiles
            if random.random() < 0.3:
                self._draw_paw_print(surface, TILE_SIZE // 2, TILE_SIZE // 2, 
                                    TILE_SIZE // 5, (color[0] - 20, color[1] - 20, color[2] - 20))
        
        elif tile_type == TILE_SWITCH:
            # Draw a cute dog bowl for switch
            pygame.draw.ellipse(surface, DOGGY_DARK_BROWN, 
                             (TILE_SIZE // 6, TILE_SIZE // 6,
                             2 * TILE_SIZE // 3, 2 * TILE_SIZE // 3))
            pygame.draw.ellipse(surface, color, 
                             (TILE_SIZE // 4, TILE_SIZE // 4,
                             TILE_SIZE // 2, TILE_SIZE // 2))
        
        elif tile_type == TILE_DOOR_CLOSED:
            # Draw a doggy door
            pygame.draw.rect(surface, DOGGY_DARK_BROWN, 
                          (2, 2, TILE_SIZE - 4, TILE_SIZE - 4), 4)
            # Door handle
            pygame.draw.circle(surface, DOGGY_BLACK, 
                            (TILE_SIZE - 10, TILE_SIZE // 2), 3)
            # Dog door flap
            pygame.draw.ellipse(surface, DOGGY_BLACK, 
                             (TILE_SIZE // 4, TILE_SIZE // 2,
                             TILE_SIZE // 2, TILE_SIZE // 3))
        
        elif tile_type == TILE_DOOR_OPEN:
            # Draw an open doggy door
            pygame.draw.rect(surface, DOGGY_DARK_BROWN, 
                          (2, 2, TILE_SIZE - 4, TILE_SIZE - 4), 2)
            # Door frame
            pygame.draw.rect(surface, DOGGY_BROWN, 
                          (4, 4, TILE_SIZE - 8, TILE_SIZE - 8), 1)
            
        elif tile_type == TILE_EXIT:
            # Draw a doggy house as exit
            # House shape
            pygame.draw.polygon(surface, DOGGY_DARK_BROWN, [
                (2, TILE_SIZE - 2),
                (2, TILE_SIZE // 2),
                (TILE_SIZE // 2, 2),
                (TILE_SIZE - 2, TILE_SIZE // 2),
                (TILE_SIZE - 2, TILE_SIZE - 2)
            ])
            # Door
            pygame.draw.rect(surface, DOGGY_BLACK, 
                          (TILE_SIZE // 3, TILE_SIZE // 2,
                           TILE_SIZE // 3, TILE_SIZE // 3))
            
        elif tile_type == TILE_PORTAL_A or tile_type == TILE_PORTAL_B:
            # Draw a teleport doggy tunnel
            for i in range(1, 6):
                radius = TILE_SIZE // 2 - (i * 2)
                width = 2 if i % 2 == 0 else 1
                pygame.draw.circle(surface, DOGGY_BLACK, 
                                (TILE_SIZE // 2, TILE_SIZE // 2), radius, width)
                
        elif tile_type == TILE_ITEM_KEY:
            # Draw a dog treat as key
            surface.fill(DOGGY_BEIGE)
            # Draw bone shape
            self._draw_bone(surface, TILE_SIZE // 2, TILE_SIZE // 2, 
                          TILE_SIZE // 2, DOGGY_YELLOW)
            
        elif tile_type == TILE_ITEM_POTION:
            # Draw a water bowl as potion
            pygame.draw.ellipse(surface, DOGGY_DARK_BROWN, 
                             (TILE_SIZE // 6, TILE_SIZE // 3,
                              2 * TILE_SIZE // 3, TILE_SIZE // 2))
            pygame.draw.ellipse(surface, DOGGY_BLUE, 
                             (TILE_SIZE // 4, TILE_SIZE // 3 + 2,
                              TILE_SIZE // 2, TILE_SIZE // 3))
            
        elif tile_type == TILE_TERMINAL:
            # Draw a dog tag as terminal
            pygame.draw.circle(surface, DOGGY_BROWN, 
                            (TILE_SIZE // 2, TILE_SIZE // 2), 
                            TILE_SIZE // 3)
            pygame.draw.circle(surface, DOGGY_YELLOW, 
                            (TILE_SIZE // 2, TILE_SIZE // 2), 
                            TILE_SIZE // 3 - 2)
            # Hole for the tag
            pygame.draw.circle(surface, DOGGY_BEIGE, 
                            (TILE_SIZE // 2, TILE_SIZE // 4), 
                            TILE_SIZE // 8)
        
        # Add a border to all tiles
        pygame.draw.rect(surface, DOGGY_DARK_BROWN, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        
        self.images[name] = surface
    
    def _draw_mini_bone(self, surface, x, y, size, color):
        """Draw a mini bone shape for patterns."""
        # Draw the middle rectangle 
        rect_width = size // 2
        rect_height = size // 4
        rect_x = x - rect_width // 2
        rect_y = y - rect_height // 2
        pygame.draw.rect(surface, color, (rect_x, rect_y, rect_width, rect_height))
        
        # Draw the circular ends
        radius = size // 6
        pygame.draw.circle(surface, color, (rect_x, rect_y + rect_height // 2), radius)
        pygame.draw.circle(surface, color, (rect_x + rect_width, rect_y + rect_height // 2), radius)
    
    def _draw_bone(self, surface, x, y, size, color):
        """Draw a larger bone shape for items."""
        # Draw the middle rectangle 
        rect_width = size
        rect_height = size // 3
        rect_x = x - rect_width // 2
        rect_y = y - rect_height // 2
        pygame.draw.rect(surface, color, (rect_x, rect_y, rect_width, rect_height))
        
        # Draw the circular ends
        radius = size // 3
        pygame.draw.circle(surface, color, (rect_x, rect_y + rect_height // 2), radius)
        pygame.draw.circle(surface, color, (rect_x + rect_width, rect_y + rect_height // 2), radius)
        
        # Add a highlight
        pygame.draw.rect(surface, DOGGY_BEIGE, (rect_x + 2, rect_y + 2, rect_width - 4, rect_height - 4), 1)
    
    def _draw_paw_print(self, surface, x, y, size, color):
        """Draw a cute paw print."""
        # Main pad
        pygame.draw.ellipse(surface, color, 
                         (x - size // 2, y - size // 2, 
                          size, size))
        
        # Toe pads - three small circles above the main pad
        toe_size = size // 3
        for i in range(3):
            toe_x = x - size // 2 + (i * toe_size)
            toe_y = y - size // 2 - toe_size // 2
            pygame.draw.circle(surface, color, (toe_x, toe_y), toe_size // 2)
    
    def _create_player_sprite(self):
        """Create a cute doggy player sprite."""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Draw the body (cute puppy)
        pygame.draw.circle(surface, DOGGY_BROWN, 
                        (TILE_SIZE // 2, TILE_SIZE // 2), 
                        TILE_SIZE // 3)  # Head/body
        
        # Ears
        ear_size = TILE_SIZE // 8
        pygame.draw.ellipse(surface, DOGGY_BROWN, 
                         (TILE_SIZE // 2 - TILE_SIZE // 3, TILE_SIZE // 4,
                          ear_size * 2, ear_size))
        pygame.draw.ellipse(surface, DOGGY_BROWN, 
                         (TILE_SIZE // 2 + TILE_SIZE // 6, TILE_SIZE // 4,
                          ear_size * 2, ear_size))
        
        # Eyes
        eye_size = TILE_SIZE // 10
        pygame.draw.circle(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2 - eye_size, TILE_SIZE // 2 - 2), 
                        eye_size // 2)
        pygame.draw.circle(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2 + eye_size, TILE_SIZE // 2 - 2), 
                        eye_size // 2)
        
        # Nose
        pygame.draw.circle(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2, TILE_SIZE // 2 + 3), 
                        eye_size // 2)
        
        # Mouth
        pygame.draw.arc(surface, DOGGY_BLACK, 
                       (TILE_SIZE // 2 - eye_size, TILE_SIZE // 2 + 3, 
                        eye_size * 2, eye_size), 
                        0, math.pi, 1)
        
        # Collar
        pygame.draw.arc(surface, DOGGY_BLUE, 
                      (TILE_SIZE // 2 - TILE_SIZE // 4, TILE_SIZE // 2 + 6, 
                       TILE_SIZE // 2, TILE_SIZE // 8), 
                       0, math.pi, 3)
        
        # Tag
        pygame.draw.circle(surface, DOGGY_YELLOW, 
                        (TILE_SIZE // 2, TILE_SIZE // 2 + 10), 
                        3)
        
        self.images["player"] = surface
        
        # Create directional versions for animation
        self._create_directional_sprites("player")
    
    def _create_directional_sprites(self, base_name):
        """Create directional versions of the sprite."""
        base_sprite = self.images[base_name]
        
        # Create flipped version for left direction
        left_sprite = pygame.transform.flip(base_sprite, True, False)
        self.images[f"{base_name}_left"] = left_sprite
        
        # Use the base sprite for right direction
        self.images[f"{base_name}_right"] = base_sprite
        
        # Create slightly modified versions for up/down
        up_sprite = base_sprite.copy()
        # Move the eyes up slightly for "looking up"
        pygame.draw.rect(up_sprite, (0, 0, 0, 0), 
                       (TILE_SIZE // 2 - TILE_SIZE // 5, TILE_SIZE // 2 - 5, 
                        TILE_SIZE // 2.5, 5))  # Clear eye area
        pygame.draw.circle(up_sprite, DOGGY_BLACK, 
                        (TILE_SIZE // 2 - TILE_SIZE // 10, TILE_SIZE // 2 - 5), 
                        TILE_SIZE // 20)
        pygame.draw.circle(up_sprite, DOGGY_BLACK, 
                        (TILE_SIZE // 2 + TILE_SIZE // 10, TILE_SIZE // 2 - 5), 
                        TILE_SIZE // 20)
        self.images[f"{base_name}_up"] = up_sprite
        
        down_sprite = base_sprite.copy()
        # No modification needed for down, use as is
        self.images[f"{base_name}_down"] = down_sprite
    
    def _create_clone_sprite(self):
        """Create a semi-transparent clone of the player sprite."""
        player_sprite = self.images["player"]
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Get pixel data
        for x in range(TILE_SIZE):
            for y in range(TILE_SIZE):
                # Get color at this pixel
                color = player_sprite.get_at((x, y))
                # Make it semi-transparent
                if color.a > 0:  # Only modify non-transparent pixels
                    transparent_color = (color.r, color.g, color.b, 128)
                    surface.set_at((x, y), transparent_color)
        
        self.images["clone"] = surface
        
        # Create directional versions
        self._create_directional_clones()
    
    def _create_directional_clones(self):
        """Create directional versions of the clone sprite."""
        for direction in ["left", "right", "up", "down"]:
            player_dir = self.images[f"player_{direction}"]
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Get pixel data
            for x in range(TILE_SIZE):
                for y in range(TILE_SIZE):
                    # Get color at this pixel
                    color = player_dir.get_at((x, y))
                    # Make it semi-transparent
                    if color.a > 0:  # Only modify non-transparent pixels
                        transparent_color = (color.r, color.g, color.b, 128)
                        surface.set_at((x, y), transparent_color)
            
            self.images[f"clone_{direction}"] = surface
    
    def _create_guard_sprite(self):
        """Create a guard dog sprite (slightly angry looking)."""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Draw the body (bigger, meaner dog)
        pygame.draw.circle(surface, DOGGY_DARK_BROWN, 
                        (TILE_SIZE // 2, TILE_SIZE // 2), 
                        TILE_SIZE // 3)  # Head/body
        
        # Pointy ears
        ear_width = TILE_SIZE // 5
        ear_height = TILE_SIZE // 3
        # Left ear
        pygame.draw.polygon(surface, DOGGY_DARK_BROWN, [
            (TILE_SIZE // 2 - TILE_SIZE // 6, TILE_SIZE // 2 - TILE_SIZE // 8),  # Base right
            (TILE_SIZE // 2 - TILE_SIZE // 3, TILE_SIZE // 2 - TILE_SIZE // 8),  # Base left
            (TILE_SIZE // 2 - TILE_SIZE // 5, TILE_SIZE // 4 - TILE_SIZE // 8),  # Tip
        ])
        # Right ear
        pygame.draw.polygon(surface, DOGGY_DARK_BROWN, [
            (TILE_SIZE // 2 + TILE_SIZE // 6, TILE_SIZE // 2 - TILE_SIZE // 8),  # Base left
            (TILE_SIZE // 2 + TILE_SIZE // 3, TILE_SIZE // 2 - TILE_SIZE // 8),  # Base right
            (TILE_SIZE // 2 + TILE_SIZE // 5, TILE_SIZE // 4 - TILE_SIZE // 8),  # Tip
        ])
        
        # Eyes (angry looking)
        eye_size = TILE_SIZE // 10
        # Left eye
        pygame.draw.circle(surface, WHITE, 
                        (TILE_SIZE // 2 - eye_size, TILE_SIZE // 2 - 2), 
                        eye_size // 1.5)
        pygame.draw.circle(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2 - eye_size - 1, TILE_SIZE // 2 - 2), 
                        eye_size // 3)
        # Right eye
        pygame.draw.circle(surface, WHITE, 
                        (TILE_SIZE // 2 + eye_size, TILE_SIZE // 2 - 2), 
                        eye_size // 1.5)
        pygame.draw.circle(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2 + eye_size + 1, TILE_SIZE // 2 - 2), 
                        eye_size // 3)
        
        # Angry eyebrows
        pygame.draw.line(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2 - eye_size - eye_size//2, TILE_SIZE // 2 - 6),
                        (TILE_SIZE // 2 - eye_size + eye_size//2, TILE_SIZE // 2 - 3), 
                        2)
        pygame.draw.line(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2 + eye_size - eye_size//2, TILE_SIZE // 2 - 3),
                        (TILE_SIZE // 2 + eye_size + eye_size//2, TILE_SIZE // 2 - 6), 
                        2)
        
        # Nose
        pygame.draw.circle(surface, DOGGY_BLACK, 
                        (TILE_SIZE // 2, TILE_SIZE // 2 + 3), 
                        eye_size // 2)
        
        # Mouth (snarling)
        pygame.draw.arc(surface, DOGGY_BLACK, 
                       (TILE_SIZE // 2 - eye_size, TILE_SIZE // 2 + 3, 
                        eye_size * 2, eye_size), 
                        math.pi, 2*math.pi, 2)
        
        # Teeth
        tooth_size = 2
        pygame.draw.rect(surface, WHITE, 
                       (TILE_SIZE // 2 - 5, TILE_SIZE // 2 + 8, 
                        tooth_size, tooth_size))
        pygame.draw.rect(surface, WHITE, 
                       (TILE_SIZE // 2 + 3, TILE_SIZE // 2 + 8, 
                        tooth_size, tooth_size))
        
        # Collar (spiky)
        collar_width = TILE_SIZE // 2
        collar_height = TILE_SIZE // 8
        collar_x = TILE_SIZE // 2 - collar_width // 2
        collar_y = TILE_SIZE // 2 + 6
        pygame.draw.rect(surface, DOGGY_PINK, 
                       (collar_x, collar_y, collar_width, collar_height))
        
        # Spikes on collar
        spike_size = 3
        for i in range(5):
            spike_x = collar_x + (i * collar_width // 4)
            pygame.draw.rect(surface, DOGGY_BLACK, 
                           (spike_x, collar_y - spike_size,
                            spike_size, spike_size))
        
        self.images["guard"] = surface
        self.images["guard_alerted"] = surface  # For now use the same sprite for both states
        
        # Create "alerted" version with red glow
        alerted = surface.copy()
        alert_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(alert_surface, (255, 0, 0, 50), 
                         (TILE_SIZE // 2, TILE_SIZE // 2), 
                         TILE_SIZE // 2)
        alerted.blit(alert_surface, (0, 0))
        self.images["guard_alerted"] = alerted
    
    def _create_paw_prints(self):
        """Create paw print animation frames."""
        frames = []
        for i in range(4):
            frame = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            alpha = 200 - i * 50  # Fade out
            self._draw_paw_print(frame, TILE_SIZE // 2, TILE_SIZE // 2, 
                                TILE_SIZE // 3, (DOGGY_DARK_BROWN[0], 
                                                DOGGY_DARK_BROWN[1], 
                                                DOGGY_DARK_BROWN[2], 
                                                alpha))
            frames.append(frame)
        
        self.animations["paw_prints"] = frames
    
    def get_image(self, name, direction=None):
        """
        Get an image by name.
        If direction is specified, get the directional version if available.
        """
        if direction and f"{name}_{direction}" in self.images:
            return self.images[f"{name}_{direction}"]
        
        return self.images.get(name, self.images.get("wall"))  # Default to wall if not found
    
    def get_font(self, size):
        """Get a font by size name."""
        return self.fonts.get(size, self.fonts.get("medium"))
    
    def get_animation_frame(self, name, frame):
        """Get a specific frame of an animation."""
        if name in self.animations:
            frames = self.animations[name]
            if 0 <= frame < len(frames):
                return frames[frame]
        
        # Return a blank surface if not found
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        return surf

assets = AssetManager() 