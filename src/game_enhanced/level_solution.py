"""
Temporal Maze - Sample Level Solution Guide

This module provides a step-by-step guide on how to solve the first level
of Temporal Maze. It can be used as a reference for new players.
"""

def get_level_solution(level_number):
    """
    Return the solution steps for a specific level.
    
    Args:
        level_number (int): The level number to get a solution for
        
    Returns:
        dict: A dictionary containing solution information
    """
    solutions = {
        1: {
            "title": "First Steps in Time",
            "objective": "Reach the exit portal by using a time clone to hold down a switch.",
            "steps": [
                "1. Move right until you reach the fork in the path.",
                "2. Go to the switch (usually up and right from the fork).",
                "3. Step on the switch to open the door temporarily.",
                "4. Press T to enter time travel mode.",
                "5. Press 3 to create a clone that will repeat your last 3 moves.",
                "6. While your clone is holding the switch, move through the now open door.",
                "7. Navigate to the exit portal (purple diamond).",
            ],
            "tips": [
                "The clone will exactly repeat your movements. Position yourself correctly before creating it.",
                "If you make a mistake, press R to restart the level.",
                "You need energy to create clones. Each clone costs 1 energy point.",
                "Guards may be patrolling. Wait for them to move away before proceeding."
            ]
        },
        2: {
            "title": "Multiple Switches",
            "objective": "Activate multiple switches simultaneously using clones.",
            "steps": [
                "1. First explore the level to locate all switches and doors.",
                "2. Activate the first switch and create a clone to hold it.",
                "3. Move to the second switch and activate it.",
                "4. Create another clone to hold the second switch.",
                "5. With both doors now open, navigate to the exit portal."
            ],
            "tips": [
                "Plan your route carefully before creating clones.",
                "You may need to collect energy potions to create multiple clones.",
                "If you get stuck, try restarting and taking a different approach."
            ]
        },
        3: {
            "title": "Guard Evasion",
            "objective": "Avoid guards while collecting keys and reaching the exit.",
            "steps": [
                "1. First observe the guard patrol patterns.",
                "2. Move carefully when guards are facing away from you.",
                "3. Collect the key to unlock the door.",
                "4. Use time clones as distractions if needed.",
                "5. Navigate through the unlocked door to the exit."
            ],
            "tips": [
                "Guards can only see in the direction they're facing.",
                "Use corners and walls to break line of sight.",
                "Timing is crucial - patience is your friend."
            ]
        }
    }
    
    return solutions.get(level_number, {"title": "Level Unavailable", "steps": ["Solution not available for this level."]})

def print_solution(level_number):
    """Print the solution for a specific level to the console."""
    solution = get_level_solution(level_number)
    
    print(f"\n=== LEVEL {level_number}: {solution['title']} ===")
    print(f"\nObjective: {solution.get('objective', 'Reach the exit')}")
    
    print("\nStep-by-Step Solution:")
    for step in solution["steps"]:
        print(f"  {step}")
    
    if "tips" in solution:
        print("\nHelpful Tips:")
        for tip in solution["tips"]:
            print(f"  • {tip}")
    
    print("\nGood luck, time traveler!\n")

if __name__ == "__main__":
    # Print solution for the first level when this script is run directly
    print_solution(1) 