import attrs
import json
import pyspiel
from typing import List, Dict
import numpy as np

from playgroundrl_envs.game_interface import PlayerInterface

from ...game_interface import GameInterface, PlayerInterface, GameParameterInterface
from ...exceptions import PlaygroundInvalidActionException
from .config import GAME_LIST


@attrs.define
class OpenSpielPlayer(PlayerInterface):
    agent_name: str = ""
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
        game_type = game.get_type()
        self.state = game.new_initial_state()
        self.advance_chance_node()
        self.num_players = len(players)
        if self.num_players > game_type.max_num_players or self.num_players < game_type.min_num_players:
            raise ValueError("Invalid number of players")
        self.players = players
        # create inverse mapping from sid to player_id using dictionary comprehension
        self.player_id_dict = {player.sid: player.player_id for player in players}
        self.is_game_over = False
        
    def advance_chance_node(self):
        while self.state.is_chance_node():
            # randomly sample a chance outcome
            outcomes = self.state.chance_outcomes()
            action_list, prob_list = zip(*outcomes)
            action = np.random.choice(action_list, p=prob_list)
            self.state.apply_action(action)

    def submit_action(self, action, player_sid="", player_id=None ):
        if player_id is None and player_sid=="":
            raise ValueError("Must specify either player ID or SID")

        if player_sid != "":
            if player_sid not in self.player_id_dict:
                raise ValueError("Invalid player SID")

            player_id_from_sid = self.player_id_dict[player_sid]
        
            if player_id != None and player_id != player_id_from_sid:
                raise ValueError("Inconsistent player ID and SID")
            else:
                player_id = player_id_from_sid

        if self.state.current_player() != player_id:
            raise ValueError("Not your turn")

        try:
            if isinstance(action, str):
                action = self.state.string_to_action(self.state.current_player(), action)
            self.state.apply_action(action)
        except pyspiel.SpielError:
            raise ValueError("Invalid move")

        self.advance_chance_node()
        self.is_game_over = self.state.is_terminal()

    def get_is_game_over(self):
        return self.is_game_over

    def get_state(self, player_sid="", player_id=-1):

        if player_sid !="":
            if player_sid not in self.player_id_dict:
                raise ValueError("Invalid player SID")

            player_id_from_sid = self.player_id_dict[player_sid]

            if player_id != -1 and player_id != player_id_from_sid:
                raise ValueError("Inconsistent player ID and SID")
            else:
                player_id = player_id_from_sid
            
        if player_id == -1:
            player_id = 0

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

    def get_player_moving_sid(self):
        return self.players[self.state.current_player()].sid
    
    def get_player_moving(self):
        return self.state.current_player()

    def get_outcome(self, player_id):
        if self.is_game_over:
            returns = self.state.returns()
            if player_id in self.players:
                return returns[player_id]
            return 0.0

    def get_legal_actions(self, player_id=None):
        if player_id == None:
            player_id = self.state.current_player()
        return self.state.legal_actions(player_id)
    
    def get_legal_actions_string(self, player_id=None):
        if player_id == None:
            player_id = self.state.current_player()
        return [self.state.action_to_string(player_id, action) for action in self.get_legal_actions(player_id)]