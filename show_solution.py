#!/usr/bin/env python3
"""
Temporal Maze - Solution Viewer

A simple script to display step-by-step solutions for Temporal Maze levels.
Run this script to get help with solving a level.
"""

import sys
import os

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = script_dir
sys.path.insert(0, project_root)

# Import the level solution module
from src.game_enhanced.level_solution import print_solution

if __name__ == "__main__":
    print("\nTEMPORAL MAZE - LEVEL SOLUTIONS")
    print("-" * 40)
    
    try:
        # Get level number from command line or prompt
        if len(sys.argv) > 1:
            level = int(sys.argv[1])
        else:
            level = int(input("Enter level number (1-3): "))
        
        if 1 <= level <= 3:
            print_solution(level)
        else:
            print("\nSorry, solutions are only available for levels 1-3.")
            print("For other levels, explore and experiment with the time travel mechanics!")
    
    except ValueError:
        print("\nPlease enter a valid level number.")
    
    print("\nTo run this script with a specific level: python show_solution.py <level_number>")
    print("For example: python show_solution.py 1\n") 