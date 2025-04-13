# Temporal Maze

A time-traveling puzzle adventure game featuring a cute doggy protagonist who can create temporal clones to solve puzzles.

## Requirements

- Python 3.6 or higher
- Pygame 2.0.1 or higher
- NumPy 1.19.0 or higher

## Installation

You can install the required dependencies automatically by using our launcher:

```bash
# This will check for dependencies and install them if needed
./check_and_run.py
```

Or you can install them manually:

```bash
pip install -r requirements.txt
```

## Running the Game

We provide several ways to run the game:

### Recommended Method:

```bash
./check_and_run.py
```

This script will:
1. Check for and install required dependencies
2. Verify that Pygame can initialize properly
3. Run the optimized version of the game

### Alternative Launchers:

1. **Optimized Version** (recommended for performance):
   ```bash
   ./run_optimized_game.py
   ```

2. **Debug Version** (if you encounter issues):
   ```bash
   ./debug_enhanced_game.py
   ```

3. **Standard Version**:
   ```bash
   ./run_enhanced_game.py
   ```

## Troubleshooting

If the game freezes or you encounter other issues:

1. Try running with automatic dependency installation:
   ```
   ./check_and_run.py
   ```

2. Check log files for errors after running the debug version:
   ```
   ./debug_enhanced_game.py
   ```
   Log files are stored in the `logs` directory.

3. Make sure you have the required dependencies installed:
   ```
   pip install pygame numpy
   ```

4. Enable debug mode during gameplay by pressing F3.

5. See `README_GAME.md` for more detailed troubleshooting steps.

## Game Controls

- **WASD/Arrow Keys**: Move the character
- **T**: Create a time clone (requires energy)
- **R**: Restart the current level
- **ESC**: Pause the game
- **H**: View game rules and help
- **F3**: Toggle debug information (in optimized version)
- **F5**: Force garbage collection (in optimized version)

## Gameplay

The goal is to navigate through time-bending mazes to reach the exit portal in each level. 
You can create temporal clones of yourself to solve puzzles requiring multiple actions to be performed simultaneously.

### Time Travel Mechanics:
- Press T to create a time clone that will repeat your past movements
- Use clones to trigger multiple switches or distract guards
- Each clone costs energy to create
- Collect energy potions to restore your time travel ability

## Development

This game was created as a learning project for game development with Python and Pygame.

## Game Concept

In Temporal Maze, you navigate a grid-based environment and manipulate time to solve puzzles. The main mechanics include:

- Moving through maze-like levels with switches, doors, and other obstacles
- Creating time clones that repeat your past actions
- Coordinating between your present self and past clones to solve puzzles
- Strategic planning of movements to ensure successful puzzle completion

## How to Play

1. Run the game using `python run_enhanced_game.py`
2. Use arrow keys or WASD to move the character
3. Press T to initiate time travel and create a clone
4. Solve puzzles by using clones to help you reach the exit

## Controls

- Arrow keys / WASD: Move player
- T: Time travel
- Q: Quit game
- R: Reset level

## Project Structure

```
TemporalMaze/
  src/
    main.py
    game_logic/
      world.py
      player.py
      time_travel.py
  maps/
    level1.txt
    level2.txt
  tests/
    test_world.py
```

To view solutions for any level (1-3):
```
./show_solution.py
```

The first level solution generally involves:
1. Finding a switch
2. Stepping on it to open a door
3. Creating a time clone to keep the switch pressed
4. Moving through the open door to reach the exit

The controls are now more responsive with one-step-at-a-time movement, making the puzzles easier to navigate. The UI is also much clearer with better organized information panels. 