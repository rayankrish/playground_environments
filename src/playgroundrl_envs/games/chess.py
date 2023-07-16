from ..game_interface import GameInterface, PlayerInterface, GameParameterInterface
from enum import Enum
import attrs
from typing import List, Dict
import json
import chess as pychess
from ..sid_util import SidSessionInfo
from ..exceptions import PlaygroundInvalidActionException


@attrs.define
class ChessPlayer(PlayerInterface):
    color: pychess.Color

    def __init__(self, sid_info, player_id):
        super().__init__(sid_info, player_id)
        self.color = None


@attrs.define(frozen=True)
class ChessParameters(GameParameterInterface):
    pass


class ChessGame(GameInterface):
    def __init__(
        self,
        game_id: str,
        players: List[ChessPlayer],
        game_type: int,
        parameters: ChessParameters,
        self_training=False,
    ):
        super().__init__(game_id, parameters, players, game_type, self_training)

        self.is_game_over = False
        self.board = pychess.Board()

        self.reward = {player.player_id: 0 for player in players}
        self.player_moving, self.player_waiting = players[0], players[1]

        # TODO: This in a better way
        self.player_moving.color = pychess.WHITE
        self.player_waiting.color = pychess.BLACK

        self.winning_player = None

    def submit_action(self, action, player_sid=""):
        # Check it's their turn
        # TODO: We can probably do this in a smoother way
        if self.player_moving.sid != player_sid:
            raise PlaygroundInvalidActionException("Not your turn")

        # The move mst be for current moving player
        player = self.player_moving

        # This check might not be strictly necessary
        if player.color != self.board.turn:
            raise PlaygroundInvalidActionException("Not your turn")

        # Expect format
        # {
        #   'uci': 'g1f3'
        # }
        action = json.loads(action)

        move_uci = action["uci"]
        move = pychess.Move.from_uci(move_uci)

        if move not in self.board.legal_moves:
            raise PlaygroundInvalidActionException("Illegal move")

        self.board.push(move)
        self.player_waiting, self.player_moving = (
            self.player_moving,
            self.player_waiting,
        )

        # check if the game is over, TODO: make this cleaner
        outcome = self.board.outcome()
        if outcome is not None:
            self.is_game_over = True
            if outcome.termination in pychess.Termination:
                for player_id in list(self.players.keys()):
                    self.reward[player_id] = (
                        1 if outcome.winner is self.players[player_id].color else -1
                    )
            else:
                for player_id in list(self.players.keys()):
                    self.reward[player_id] = 0

        return True

    def get_is_game_over(self):
        return self.is_game_over

    def get_state(self, player_sid="", player_id=None):
        if player_id == None:
            player_id = self.player_moving.player_id

        state = {
            # FEN is a standard for board representation
            "fen": self.board.fen(),
            "player_moving": self.player_moving.user_id,
            "model_name": self.player_moving.model_name,
            "player_moving_id": self.player_moving.player_id,
            "player_id": player_id
            # TODO: We might want other game state here
        }
        return json.dumps(state), self.reward[player_id]

    @staticmethod
    def get_game_name():
        return "chess"

    @staticmethod
    def get_num_players():
        return 2

    def get_player_moving(self):
        return self.player_moving

    def get_outcome(self, player_id):
        # TODO: Claim draw
        outcome = self.board.outcome()
        player = self.players[player_id]

        if outcome is None:
            return None

        if outcome.termination == pychess.Termination.CHECKMATE:
            if outcome.winner is player.color:
                return 1
            return 0
        return 0.5
