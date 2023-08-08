import unittest
from playgroundrl_envs.games.codenames.codenames import (
    CodenamesPlayer,
    CodenamesGame,
    CodenamesParameters,
)

class TestCodenamesDefinition(unittest.TestCase):
    def test_simple_definition(self):
        # assert error
        with self.assertRaises(Exception):
            CodenamesPlayer()

        with self.assertRaises(Exception):
            CodenamesGame()

        # No error
        CodenamesParameters()
    

if __name__ == '__main__':
    unittest.main()

