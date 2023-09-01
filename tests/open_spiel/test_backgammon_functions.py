import unittest
from playgroundrl_envs.games.open_spiel.backgammon import BackgammonGame
from playgroundrl_envs.games.open_spiel.generic import OpenSpielPlayer

from playgroundrl_envs.sid_util import SidSessionInfo
import json


def create_default_game():
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
        OpenSpielPlayer(
            player_id=0,
            session_info=session_info1,
        ),
        OpenSpielPlayer(
            player_id=1,
            session_info=session_info2,
        ),
    ]

    game = BackgammonGame(
        game_id=0,
        players=players,
        game_type=0,
    )

    return game

def print_observation(game):
    state_dict = json.loads(game.get_state()[0])
    print(state_dict["observation_string"])


class TestBackgammonDefinition(unittest.TestCase):

    def test_get_state_validity(self):
        game = create_default_game()

        game.get_state()
        game.get_legal_actions()
        game.get_legal_actions(1)
        
        game.get_state("sid-1")
        game.get_state("sid-0")
        
        with self.assertRaises(Exception):
            game.get_state("sid-2")
        
        with self.assertRaises(Exception):
            game.get_state("sid-3")
        
        with self.assertRaises(Exception):
            game.get_state("Never gonna give you up")
        

        game.get_state("sid-1", player_id=1)
        game.get_state("sid-0", player_id=0)

        
        with self.assertRaises(Exception):
            game.get_state("sid-1", player_id=0)

        with self.assertRaises(Exception):
            game.get_state("sid-0", player_id=1)

        with self.assertRaises(Exception):
            game.get_state("sid-1", player_id=2)


    def test_get_action_validity(self):

        game = create_default_game()
        
        print("Starting game")
        print(game.get_player_moving())

        print_observation(game)

        #submit action
        while not game.get_is_game_over():
            player = game.get_player_moving()
            valid_actions = game.get_legal_actions(player)
            print(valid_actions)
            valid_action = valid_actions[0]
            game.submit_action(valid_action, player_id=player)
            print_observation(game)

        
if __name__ == "__main__":
    unittest.main()
