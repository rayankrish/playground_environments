import json
import pyspiel
from .generic import OpenSpielGame, OpenSpielParameters


class BackgammonGame(OpenSpielGame):
    def __init__(self, game_id, players, game_type, self_training=False):
        super().__init__(
            game_id,
            players,
            game_type,
            OpenSpielParameters(game_name="backgammon"),
            self_training
        )
