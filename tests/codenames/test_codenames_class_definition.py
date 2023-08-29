import unittest
from playgroundrl_envs.games.codenames.codenames import (
    CodenamesPlayer,
    CodenamesGame,
    CodenamesParameters,
)

from playgroundrl_envs.sid_util import SidSessionInfo


class TestCodenamesDefinition(unittest.TestCase):
    def test_simple_definition(self):
        # assert error
        with self.assertRaises(Exception):
            CodenamesPlayer()

        with self.assertRaises(Exception):
            CodenamesGame()

        # No error
        CodenamesParameters()


    def test_full_definition(self):        
        params = CodenamesParameters()

        session_info1 = SidSessionInfo(
            sid='sid-0',
            user_id=0,
            is_human=False,
        )

        session_info2 = SidSessionInfo(
            sid='sid-1',
            user_id=1,
            is_human=False,
        )

        players = [
            CodenamesPlayer(
                player_id=0,
                session_info=session_info1,
            ),
            CodenamesPlayer(
                player_id=1,
                session_info=session_info2,
            ),
        ]

        games = CodenamesGame(
            game_id=0,
            parameters=params,
            players=players,
            game_type=0,
        )

    

if __name__ == '__main__':
    unittest.main()

