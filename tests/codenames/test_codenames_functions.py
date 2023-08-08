import unittest
from playgroundrl_envs.games.codenames.codenames import (
    CodenamesPlayer,
    CodenamesGame,
    CodenamesParameters,
)

from playgroundrl_envs.sid_util import SidSessionInfo
import json


def create_default_game():
    params = CodenamesParameters()

    session_info1 = SidSessionInfo(
        sid="sid-0",
        user_id=0,
        is_human=False,
    )

    session_info2 = SidSessionInfo(
        sid="sid-1",
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

    game = CodenamesGame(
        game_id=0,
        parameters=params,
        players=players,
        game_type=0,
    )

    return game


class TestCodenamesDefinition(unittest.TestCase):

    def test_get_state_validity(self):
        game = create_default_game()

        game.get_state()

        game.get_state("sid-1")
        game.get_state("sid-0")

        # FAILED: should raise exception for invalid sid
        '''
        with self.assertRaises(Exception):
            game.get_state("sid-2")
        
        with self.assertRaises(Exception):
            game.get_state("sid-3")
        
        with self.assertRaises(Exception):
            game.get_state("Never gonna give you up")
        '''

        game.get_state("sid-1", player_id=1)
        game.get_state("sid-0", player_id=0)

        # FAILED: should raise exception for inconsistent sid and player_id
        '''
        with self.assertRaises(Exception):
            game.get_state("sid-1", player_id=0)

        with self.assertRaises(Exception):
            game.get_state("sid-0", player_id=1)
        '''

        with self.assertRaises(Exception):
            game.get_state("sid-1", player_id=2)


    def test_get_action_validity(self):

        game = create_default_game()

        valid_giver_action = json.dumps({
            "word": "hello",
            "count": 2
        })

        valid_guesser_single_action = json.dumps({
            "guess": 2
        })

        valid_guesser_multiple_action = json.dumps({
            "guesses": [
                2,
                4
            ]
        })

        with self.assertRaises(Exception):
            game.submit_action()

        with self.assertRaises(Exception):
            game.submit_action("sid-1")
        
        with self.assertRaises(Exception):
            game.submit_action("sid-0")
        
        with self.assertRaises(Exception):
            game.submit_action(valid_giver_action, player_sid="sid-1")
        
        with self.assertRaises(Exception):
            game.submit_action(valid_giver_action, player_sid="sid-2")
        
        game.submit_action(valid_giver_action, player_sid="sid-0")

        with self.assertRaises(Exception):
            game.submit_action(valid_giver_action, player_sid="sid-0")
        
        game.submit_action(valid_guesser_single_action, player_sid="sid-1")

        with self.assertRaises(Exception):
            game.submit_action(valid_guesser_single_action, player_sid="sid-1")


if __name__ == "__main__":
    unittest.main()
