import os
import sys
import unittest

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from game_logic.world import World

class TestWorld(unittest.TestCase):
    def setUp(self):
        """Set up a test world"""
        # Create a test map file
        self.test_map_path = os.path.join(os.path.dirname(__file__), 'test_map.txt')
        with open(self.test_map_path, 'w') as f:
            f.write('#####\n')
            f.write('#.S.#\n')
            f.write('#.D.#\n')
            f.write('#.E.#\n')
            f.write('#####\n')
        
        # Create a world instance
        self.world = World(self.test_map_path)
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove the test map file
        if os.path.exists(self.test_map_path):
            os.remove(self.test_map_path)
    
    def test_world_dimensions(self):
        """Test world dimensions are correct"""
        self.assertEqual(self.world.width, 5)
        self.assertEqual(self.world.height, 5)
    
    def test_tile_access(self):
        """Test we can access tiles correctly"""
        self.assertEqual(self.world.get_tile(0, 0), '#')  # Wall
        self.assertEqual(self.world.get_tile(1, 1), '.')  # Floor
        self.assertEqual(self.world.get_tile(2, 1), 'S')  # Switch
        self.assertEqual(self.world.get_tile(2, 2), 'D')  # Door
        self.assertEqual(self.world.get_tile(2, 3), 'E')  # Exit
    
    def test_walkable(self):
        """Test walkable tiles"""
        self.assertFalse(self.world.is_walkable(0, 0))  # Wall is not walkable
        self.assertTrue(self.world.is_walkable(1, 1))   # Floor is walkable
        self.assertTrue(self.world.is_walkable(2, 1))   # Switch is walkable
        self.assertFalse(self.world.is_walkable(2, 2))  # Door is not walkable (initially closed)
    
    def test_switch_and_door(self):
        """Test switch activates door"""
        # Initially door is closed
        self.assertFalse(self.world.is_walkable(2, 2))
        
        # Activate switch
        self.world.activate_switch(2, 1)
        
        # Door should be open now
        self.assertTrue(self.world.is_walkable(2, 2))
        
        # Deactivate switch
        self.world.deactivate_switch(2, 1)
        
        # Door should be closed again
        self.assertFalse(self.world.is_walkable(2, 2))
    
    def test_exit_detection(self):
        """Test exit detection"""
        self.assertTrue(self.world.is_exit(2, 3))
        self.assertFalse(self.world.is_exit(1, 1))

if __name__ == '__main__':
    unittest.main() 