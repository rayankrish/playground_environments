import random
from ...game_interface import GameInterface, PlayerInterface, GameParameterInterface
from enum import Enum
import attrs
from typing import List, Dict
import json
from catanatron.game import Game as CatanatronGame
from catanatron.models.player import Color, Player as CatanatronPlayer
from catanatron.models.actions import *
from catanatron.models.enums import *
from catanatron.state import State
from catanatron.json import GameEncoder, action_from_json
import json
from ...sid_util import SidSessionInfo
from .encoder import CustomGameEncoder
import attrs


@attrs.define
class CatanPlayer(PlayerInterface):
    color: Color
    """Catanatron color of player"""

    catanatron_player: CatanatronPlayer
    """Easy way to access catanatron player """

    def __init__(self, sid_info, player_id):
        super().__init__(sid_info, player_id)
        # TODO: Better initialization
        self.color = None
        self.catanatron_player = None


@attrs.define(frozen=True)
class CatanParameters(GameParameterInterface):
    pass


class CatanGame(GameInterface):
    def __init__(
        self,
        game_id,
        players: List[SidSessionInfo],
        game_type,
        parameters: GameParameterInterface,
        self_training=False,
    ):
        super().__init__(game_id, parameters, players, game_type, self_training)

        # ONLY SUPPORT UP TO FOUR PEOPLE FOR NOW
        assert len(players) < 4

        self.reward = {player.player_id: 0 for player in players}
        # TODO: This in a better way

        colors = [Color.BLUE, Color.ORANGE, Color.RED, Color.WHITE]
        catanatron_players = []

        self.color_to_player_map = {}  # Will make it easier to look people up by color
        for i, player in enumerate(players):
            # Add a bunch of helpful information to each player class
            # TODO: Probably should add state to classes in a better way
            player.color = colors[i]
            catanatron_player = CatanatronPlayer(color=colors[i])
            player.catanatron_player = catanatron_player

            # Update list of player objects
            catanatron_players.append(catanatron_player)
            self.color_to_player_map[colors[i]] = player

        self.winning_player = None

        # Initialize game
        # TODO: Anything else configurable (VPs, discard limit? )
        # TODO: Potentially disable 1000 turn limit
        self.game = CatanatronGame(catanatron_players)

        self.encoder = CustomGameEncoder(self.game)

        # stupid hack to see game in the middle
        # for i in range(105):
        #     action = self.game.state.playable_actions[0]

        self.is_game_over = False

    def submit_action(self, action, player_sid=""):
        # player = self.players[player_sid]
        # Get
        player = self.get_player_moving()

        if player.sid != player_sid:
            return False

        # Currently, data just comes in as a JSON *Array*
        # Expects it in the format [Color, Action_Type, Value]
        # Color and Action_Type are strings, Value is depedent on
        # the ACTION_TYPE. Should be consistent with catanatron format.

        # TODO: More in depth error checking
        # action_data = json.loads(action)

        # Convert back to catanatron format
        action = self.encoder.unconvert_action(action, player.color)

        _action_done = self.game.execute(action)

        return True

    def get_state(self, player_sid="", player_id=-1):
        # Hack to get all game data into an easy-to-process dictionary
        player_moving: SidSessionInfo = self.get_player_moving()

        if player_id == -1:
            player = player_moving
        else:
            player = self.players[player_id]

        """
        if player_sid != player.sid:
            # TODO: Raise this exception
            raise Exception("Not able to query state for this player")
        """

        state_dict = self.encoder.convert_state(self.game, player.player_id)
        state_dict["player_moving"] = player_moving.user_id
        state_dict["model_name"] = player_moving.model_name
        state_dict["player_moving_id"] = player_moving.player_id

        state_json = json.dumps(state_dict)  # No need for custom encoder

        # TODO: Reward
        return state_json, 0

    @staticmethod
    def get_game_name():
        return "catan"

    @staticmethod
    def get_num_players():
        return 3

    def get_is_game_over(self):
        return self.is_game_over

    def get_outcome(self, player_sid):
        # TODO: Outcomes
        return 0.5

    def get_player_moving(self):
        return self.color_to_player_map[self.game.state.current_color()]


if __name__ == "__main__":
    # Small test to check get state and action
    # TODO: Move to a test file

    players = [SidSessionInfo(str(i), str(i), True) for i in range(3)]
    cg = CatanGame("testid", players, "catan")
    states = []

    for i in range(500):
        s, _ = cg.get_state(str(0))
        s = json.loads(s)
        current_sid = s["player_moving"]

        s, _ = cg.get_state(player_sid=current_sid)
        s = json.loads(s)
        actions = s["playable_actions"]

        states.append(s)

        action = actions[random.randrange(0, len(actions))]
        cg.submit_action(json.dumps(action), current_sid)

    with open("state_list.json", "w") as f:
        f.write(json.dumps(states))
