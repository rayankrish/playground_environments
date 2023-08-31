import attrs
import json
import pyspiel
from typing import List, Dict

from ..game_interface import GameInterface, PlayerInterface, GameParameterInterface
from ..exceptions import PlaygroundInvalidActionException
from .config import GAME_LIST

class OpenSpielPlayer(PlayerInterface):
    def __init__(self, sid_info, player_id):
        super().__init__(sid_info, player_id)

@attrs.define(frozen=True)
class OpenSpielParameters(GameParameterInterface):
    game_name: str

class OpenSpielGame(GameInterface):
    def __init__(
        self,
        game_id: str,
        players: List[OpenSpielPlayer],
        game_type: int,
        parameters: OpenSpielParameters,
        self_training=False,
    ):
        super().__init__(game_id, parameters, players, game_type, self_training)

        self.game_name = parameters.game_name
        if self.game_name not in GAME_LIST:
            raise ValueError("Invalid game name")

        game = pyspiel.load_game(self.game_name)
        self.state = game.new_initial_state()
        self.num_players = len(players)
        if self.num_players > game.max_num_players or self.num_players < game.min_num_players:
            raise ValueError("Invalid number of players")
        self.players = players
        # create inverse mapping from sid to player_id using dictionary comprehension
        self.player_id_dict = {player.sid: player.player_id for player in players}
        self.is_game_over = False
        

    def submit_action(self, action, player_sid):
        
        if player_sid not in self.player_id_dict:
            raise ValueError("Invalid player SID")

        player_id = self.player_id_dict[player_sid]

        if self.state.current_player() != player_id:
            raise ValueError("Not your turn")

        try:
            action = self.state.string_to_action(self.state.current_player(), action)
            self.state.apply_action(action)
        except pyspiel.SpielError:
            raise ValueError("Invalid move")

        self.is_game_over = self.state.is_terminal()

    def get_is_game_over(self):
        return self.is_game_over

    def get_state(self, player_id):
        if player_id not in self.players:
            raise ValueError("Invalid player ID")

        state = {
            "observation_string": self.state.observation_string(player_id),
            "observation_tensor": self.state.observation_tensor(player_id),
            "player_moving": self.state.current_player(),
        }
        reward = 0.0  # TODO: specify reward
        return json.dumps(state), reward

    def get_game_name(self):
        return self.game_name

    def get_num_players(self):
        return self.num_players

    def get_player_moving(self):
        return self.players[self.state.current_player()].sid

    def get_outcome(self, player_id):
        if self.is_game_over:
            returns = self.state.returns()
            if player_id in self.players:
                return returns[player_id]
            return 0.0

