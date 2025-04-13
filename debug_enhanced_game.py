#!/usr/bin/env python3
"""
Debugging script for the enhanced Temporal Maze game.
This script provides error handling and performance monitoring
to help identify why the game might be freezing.
"""

import os
import sys
import time
import traceback
import logging
from datetime import datetime

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"game_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    logging.info("Starting game with debugging enabled")
    
    # Patch pygame to add performance monitoring
    import pygame
    original_display_flip = pygame.display.flip
    frame_times = []
    last_frame_time = time.time()
    
    def monitored_flip():
        """Wrapper for pygame.display.flip() to monitor frame rate"""
        global last_frame_time, frame_times
        current_time = time.time()
        frame_time = current_time - last_frame_time
        frame_times.append(frame_time)
        
        # Log slowdowns
        if frame_time > 0.1:  # More than 100ms (less than 10 FPS)
            logging.warning(f"Slow frame: {frame_time:.4f}s ({1/frame_time:.1f} FPS)")
        
        # Calculate and log FPS every 5 seconds
        if len(frame_times) >= 100:
            avg_frame_time = sum(frame_times) / len(frame_times)
            avg_fps = 1 / avg_frame_time if avg_frame_time > 0 else 0
            logging.info(f"Average FPS: {avg_fps:.2f}")
            frame_times = []
        
        last_frame_time = current_time
        return original_display_flip()
    
    pygame.display.flip = monitored_flip
    
    # Import and run the game
    from src.game_enhanced.main import main
    
    logging.info("Game initialized, starting main loop")
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    logging.critical(f"Game crashed: {str(e)}")
    logging.critical(traceback.format_exc())
    
    # Also print to console
    print(f"ERROR: Game crashed! See log file for details: {log_file}")
    print(f"Exception: {str(e)}")
    traceback.print_exc()
    
finally:
    logging.info("Game session ended")
    print(f"Debug log saved to: {log_file}") 