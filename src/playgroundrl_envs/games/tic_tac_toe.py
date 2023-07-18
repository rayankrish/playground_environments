from ..game_interface import GameInterface, PlayerInterface, GameParameterInterface
import json
import attrs

EMPTY_SQUARE = -1


def check_winning_board(board):
    for i in range(3):
        if (
            board[i][0] == board[i][1]
            and board[i][1] == board[i][2]
            and board[i][0] != EMPTY_SQUARE
        ):
            return True
        if (
            board[0][i] == board[1][i]
            and board[1][i] == board[2][i]
            and board[0][i] != EMPTY_SQUARE
        ):
            return True
    if (
        board[0][0] == board[1][1]
        and board[1][1] == board[2][2]
        and board[0][0] != EMPTY_SQUARE
    ):
        return True
    if (
        board[0][2] == board[1][1]
        and board[1][1] == board[2][0]
        and board[0][2] != EMPTY_SQUARE
    ):
        return True
    return False


board_squares = [(a, b) for a in range(3) for b in range(3)]


class TicTacToePlayer(PlayerInterface):
    pass


@attrs.define(frozen=True)
class TicTacToeParameters(GameParameterInterface):
    pass


class TicTacToeGame(GameInterface):
    def __init__(
        self,
        game_id,
        players,
        game_type,
        parameters: TicTacToeParameters,
        self_training=False,
    ):
        super().__init__(game_id, parameters, players, game_type, self_training)
        self.is_game_over = False

        # -1 empty, 0 for player 1, 1 for player 2
        self.board = [[EMPTY_SQUARE for i in range(3)] for j in range(3)]

        self.reward = {player.player_id: 0 for player in players}
        self.player_moving, self.player_waiting = players[0], players[1]
        self.winning_player = None

    def submit_action(self, action, player_sid=""):
        if self.player_moving.sid != player_sid:
            # Assert the socket has the right to make actions for this player
            return False

        # action should be a string "0" to "8" for the possible squares
        x, y = board_squares[int(action)]
        if self.board[x][y] != EMPTY_SQUARE:
            return False

        # Submit action on behalf of the player who's turn it is
        player_id = self.player_moving.player_id

        # Player IDs are zero indexed, but on the board it's 1-indexed
        self.board[x][y] = player_id

        if check_winning_board(self.board):
            self.reward[player_id] = 1
            self.reward[self.player_waiting.player_id] = -1
            self.is_game_over = True
            self.winning_player = player_id

        if self.iteration >= 8:
            # draw
            self.is_game_over = True

        self.player_moving, self.player_waiting = (
            self.player_waiting,
            self.player_moving,
        )
        return True

    def get_state(self, player_sid="", player_id=-1):
        if player_id == -1:
            player_id = self.player_moving.player_id

        # Return as JSON so it's very easy to parse
        return (
            json.dumps(
                {
                    "player_moving": self.player_moving.user_id,
                    "model_name": self.player_moving.model_name,
                    "player_moving_id": self.player_moving.player_id,
                    "board": self.board,
                }
            ),
            self.reward[player_id],
        )

    @staticmethod
    def get_game_name():
        return "tic_tac_toe"

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
