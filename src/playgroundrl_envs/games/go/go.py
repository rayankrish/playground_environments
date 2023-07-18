from enum import Enum
from ...game_interface import GameInterface, GameParameterInterface, PlayerInterface
import json
from .engine import gogame as go_engine
import numpy as np
import attrs
from ...exceptions import PlaygroundInvalidActionException


EMPTY_SQUARE = -1


class Color(Enum):
    WHITE = 0
    BLACK = 1


class GoPlayer(PlayerInterface):
    color: Color


@attrs.define(frozen=True)  # Makes it hashable, but not mutatable
class GoParameters(GameParameterInterface):
    board_size: int = 15


class GoGame(GameInterface):
    def __init__(
        self, game_id, players, game_type, parameters: GoParameters, self_training=False
    ):
        super().__init__(game_id, parameters, players, game_type, self_training)

        self.reward = {player.player_id: 0 for player in players}
        self.player_moving, self.player_waiting = players[0], players[1]

        # Black is always player 0
        self.players[0].color = Color.BLACK
        self.players[1].color = Color.WHITE

        self.winning_player = None

        self.board_size = parameters.board_size

        # See engine/gogame.py for definition
        self.state: np.Array = go_engine.init_state(self.board_size)

        self.is_game_over = False

    def submit_action(self, action, player_sid=""):
        if self.player_moving.sid != player_sid:
            # Assert the socket has the right to make actions for this player
            raise PlaygroundInvalidActionException("It is not your turn.")

        # Should be int representing action
        action = int(action)

        try:
            self.state = go_engine.next_state(self.state, action)
        except AssertionError:
            raise PlaygroundInvalidActionException("You cannot place a piece there.")

        black_area, white_area = go_engine.areas(self.state)

        self.reward[0] = black_area
        self.reward[1] = white_area

        if go_engine.game_ended(self.state) == 1:
            self.is_game_over = True
            if self.reward[0] > self.reward[1]:
                self.winning_player = 0
            elif self.reward[1] > self.reward[0]:
                self.winning_player = 1
            else:
                self.winning_player = None

        self.player_moving, self.player_waiting = (
            self.player_waiting,
            self.player_moving,
        )
        return True

    def get_state(self, player_sid="", player_id=-1):
        if player_id == -1:
            player_id = self.player_moving.player_id

        board = self.state[0] - 1
        board += self.state[1] * 2

        move_was_pass = bool(self.state[4][0][0] == 1)
        invalid_moves = self.state[3]

        # Return as JSON so it's very easy to parse
        # TODO: Pot4entially an option
        return (
            json.dumps(
                {
                    "player_moving": self.player_moving.user_id,
                    "model_name": self.player_moving.model_name,
                    "player_moving_id": self.player_moving.player_id,
                    "board": board.tolist(),
                    "invalid_moves": invalid_moves.tolist(),
                    "last_move_was_pass": move_was_pass,
                }
            ),
            self.reward[player_id],
        )

    @staticmethod
    def get_game_name():
        return "go"

    @staticmethod
    def get_num_players():
        return 2

    def get_player_moving(self):
        return self.player_moving

    def get_is_game_over(self):
        return self.is_game_over

    def get_outcome(self, player_id):
        if not self.is_game_over:
            return None
        if self.winning_player is None:
            return 0.5
        if self.winning_player == player_id:
            return 1
        return 0
