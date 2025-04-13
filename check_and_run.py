#!/usr/bin/env python3
"""
Launcher script that checks for dependencies and installs them if missing,
then runs the optimized version of the Temporal Maze game.
"""

import os
import sys
import subprocess
import platform

def check_and_install_dependencies():
    """Check for required dependencies and install them if missing."""
    print("Checking for required dependencies...")
    
    try:
        # Check for pip
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Error: pip is not installed. Please install pip first.")
        sys.exit(1)
    
    # Required packages
    required_packages = {
        "pygame": "pygame>=2.0.1",
        "numpy": "numpy>=1.19.0"
    }
    
    missing_packages = []
    
    # Check each package
    for package, requirement in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing")
            missing_packages.append(requirement)
    
    # Install missing packages
    if missing_packages:
        print("\nInstalling missing dependencies...")
        for package in missing_packages:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                                     stdout=subprocess.PIPE)
                print(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"Error installing {package}: {e}")
                print("Please try installing it manually using:")
                print(f"  pip install {package}")
                sys.exit(1)
    
    print("\nAll dependencies are installed. Ready to run the game!\n")

def check_pygame_initialization():
    """Test pygame initialization to catch early errors."""
    try:
        import pygame
        pygame.init()
        
        # Get info about the display 
        try:
            drivers = pygame.display.get_drivers()
            print(f"Available display drivers: {', '.join(drivers)}")
        except AttributeError:
            # get_drivers might not be available in newer Pygame versions
            print(f"Pygame version: {pygame.version.ver}")
            print("Using default display driver")
            
        # Try creating a small window to test display
        try:
            flags = 0
            # Use HIDDEN flag if available (newer Pygame versions)
            if hasattr(pygame, 'HIDDEN'):
                flags = pygame.HIDDEN
            
            test_surface = pygame.display.set_mode((100, 100), flags=flags)
            pygame.display.quit()
            print("✓ Pygame display initialized successfully")
            return True
        except Exception as e:
            print(f"Warning: Could not initialize test display: {e}")
            print("Attempting to continue anyway...")
            return True
    except Exception as e:
        print(f"Error initializing Pygame: {e}")
        print("This might be due to missing display drivers or an unsupported system configuration.")
        return False

def run_game():
    """Run the optimized game."""
    print("Starting Temporal Maze game...")
    
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Import the optimized game class
    try:
        from src.game_enhanced.optimized_game import OptimizedGame
        
        # Initialize and run the game
        game = OptimizedGame()
        game.run()
    except Exception as e:
        print(f"Error running the game: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nTry running the debug script to log more information:")
        print("  python debug_enhanced_game.py")
        sys.exit(1)

if __name__ == "__main__":
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    
    check_and_install_dependencies()
    
    if check_pygame_initialization():
        run_game()
    else:
        print("\nPygame initialization failed. The game may not run correctly.")
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() in ['y', 'yes']:
            run_game()
        else:
            print("Exiting. Please ensure your system supports Pygame.")
            sys.exit(1) 