# Temporal Maze

A puzzle game where you solve mazes by creating time clones of yourself.

## Game Concept

In Temporal Maze, you navigate through puzzles by strategically placing switches, opening doors, and most importantly, using the ability to create "time clones" of yourself.

These clones follow the exact path you've taken in the past, allowing you to be in multiple places at once. Use this mechanic to hold down switches, trigger mechanisms, and solve complex puzzles.

## Features

- Graphical interface with smooth animation
- Multiple levels with increasing difficulty
- Time travel mechanics that create clones to follow your past movements
- Various puzzle elements:
  - Switches that open doors
  - Keys that unlock barriers
  - Time-specific objects (exist only in past or present)
  - Teleporters
- Interactive tutorial

## Controls

- **WASD/Arrow Keys**: Move character
- **T**: Initiate time travel (create a clone)
- **R**: Reset level
- **ESC**: Pause/Menu

## Installation

1. Make sure you have Python 3.6+ and Pygame installed:
   ```
   pip install -r requirements.txt
   ```

2. Run the game:
   ```
   python src/main.py
   ```

## How to Play

1. **Movement**: Navigate through the maze using WASD or arrow keys.
2. **Switches**: Step on switches (yellow tiles) to open corresponding doors.
3. **Time Travel**: Press T to create a clone that follows your past movements.
   - When prompted, enter how many steps back you want to go.
   - Your clone will repeat everything you did from that point.
4. **Multiple Clones**: Create up to 3 clones to solve complex puzzles.
5. **Goal**: Reach the exit (green star) in each level.

## Level Design

- **Level 1**: Tutorial level teaching basic mechanics
- **Level 2**: Introduces multiple switch/door combinations
- **Level 3**: Advanced puzzles requiring multiple time clones

## Credits

Developed using:
- Python
- Pygame

---

*Can you master the power of time and escape the Temporal Maze?* 