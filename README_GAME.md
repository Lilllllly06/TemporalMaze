# Temporal Maze Game Launcher Scripts

This document explains the different launcher scripts available for the Temporal Maze game and how to troubleshoot freezing issues.

## Available Launcher Scripts

### 1. Standard Game Launcher
```
./run_enhanced_game.py
```
This script launches the standard version of the Temporal Maze game.

### 2. Optimized Game Launcher
```
./run_optimized_game.py
```
Use this script if you experience freezing or performance issues with the standard launcher. The optimized version includes:
- Improved rendering performance
- Memory optimization
- Frame rate stabilization
- Viewport culling (only rendering what's visible)
- Debug information (press F3 to toggle)

### 3. Debug Game Launcher
```
./debug_enhanced_game.py
```
This launcher runs the game with extensive logging and performance monitoring. It creates log files in the `logs` directory that can help identify the cause of any freezing issues.

## Troubleshooting Freezing Issues

If you experience freezing while playing the Temporal Maze game, try these solutions in order:

1. **Use the optimized launcher**: 
   ```
   ./run_optimized_game.py
   ```
   
2. **Check system resources**:
   Make sure your system has sufficient memory and CPU resources available.

3. **Enable debug mode**:
   Press F3 while running the optimized version to see performance metrics.

4. **Run with debugging**:
   ```
   ./debug_enhanced_game.py
   ```
   After encountering a freeze, check the log files in the `logs` directory for clues.

5. **Memory cleanup**:
   Press F5 while running the optimized version to force garbage collection.

## Common Causes of Freezing

1. **Memory leaks**: The game might accumulate too many objects over time.
2. **Rendering bottlenecks**: Too many objects being rendered at once.
3. **Infinite loops**: Game logic might get caught in an infinite loop.
4. **Resource loading**: Large assets may cause temporary freezes when loaded.

The optimized version addresses these issues through:
- Periodic garbage collection
- Viewport culling (only rendering visible objects)
- Frame time caps to prevent infinite loops
- Performance monitoring

## Additional Notes

- The game is designed to run at 60 FPS but will function properly at lower frame rates.
- If you encounter persistent issues, try reducing the game's window size or closing other applications.
- Debug logs are automatically saved with timestamps for later analysis. 