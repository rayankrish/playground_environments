from ..game_interface import GameInterface, PlayerInterface, GameParameterInterface
from typing import List, Dict
import importlib
import attrs
import codecs
import pickle
from PIL import Image
import io
import base64
from pettingzoo.classic import connect_four_v3
from ..exceptions import PlaygroundInvalidActionException


class PettingZooPlayer(PlayerInterface):
    def __init__(self, sid_info, player_id):
        super().__init__(sid_info, player_id)
        self.agent_name = None


@attrs.define(frozen=True)
class PettingZooParameters(GameParameterInterface):
    family: str
    game_name: str


class PettingZooGame(GameInterface):
    def __init__(
        self,
        game_id: str,
        players: List[PettingZooPlayer],
        game_type: int,
        parameters: PettingZooParameters,
        self_training=False,
    ):
        super().__init__(game_id, parameters, players, game_type, self_training)

        self.is_game_over = False

        self.family = parameters.family  # "classic"
        self.game_name = parameters.game_name  # "connect_four_v3"
        self.module = importlib.import_module(
            "pettingzoo." + self.family + "." + self.game_name
        )
        self.env = self.module.env(
            render_mode="rgb_array"
        )  # TODO: don't do this unless we need it
        self.env.reset()
        self.state = self.env.last()

        for i, agent in enumerate(self.env.agents):
            players[i].agent_name = agent

        # for now, just assign the player moving sequentially
        # TODO: check if this generalizes for all games
        self.player_moving_index = 0
        self.player_ids = list(self.players.keys())

    def submit_action(self, raw_action, player_sid=""):
        curr_player = self.players[self.player_ids[self.player_moving_index]]
        if curr_player.sid != player_sid:
            # Assert the socket has the right to make actions for this player
            raise PlaygroundInvalidActionException("Not player's turn")

        # parse the action
        action = pickle.loads(codecs.decode(raw_action.encode(), "base64"))
        print(type(action))

        self.env.step(action)  # TODO: check if this was performed smoothly
        self.state = self.env.last()
        if self.state[-3] or self.state[-2]:
            self.is_game_over = True

        self.player_moving_index += 1
        if self.player_moving_index == len(self.player_ids):
            self.player_moving_index = 0

        return True

    def get_state(self, player_sid="", player_id=0):
        # TODO: see if we need to change this based on the player accessing it
        pickled = codecs.encode(pickle.dumps(self.state), "base64").decode()
        return pickled, float(self.state[1])

    def get_render(self):
        im = Image.fromarray(self.env.render())
        buffered = io.BytesIO()
        im.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue())

    def get_is_game_over(self):
        return self.is_game_over

    @staticmethod
    def get_game_name():
        return "petting_zoo"

    @staticmethod
    def get_num_players():
        return 2

    def get_outcome(self, player_id):
        pass

    def get_player_moving(self) -> PlayerInterface:
        return self.players[self.player_ids[self.player_moving_index]]
