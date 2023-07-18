from ..game_interface import GameInterface, PlayerInterface, GameParameterInterface
import random
import json
import attrs
from ..exceptions import PlaygroundInvalidActionException

NUM_TILES_PER_SIDE = 10


# Static function
def is_within_screen(_snake):
    head_x, head_y = _snake[-1]
    return 0 <= head_x < NUM_TILES_PER_SIDE and 0 <= head_y < NUM_TILES_PER_SIDE


def is_not_overlapping(_snake):
    head = _snake[-1]
    tail = _snake[:-1]
    return head not in tail


class SnakePlayer(PlayerInterface):
    pass


@attrs.define(frozen=True)
class SnakeParameters(GameParameterInterface):
    pass


class SnakeGame(GameInterface):
    def __init__(
        self,
        game_id,
        players,
        game_type,
        parameters: SnakeParameters,
        self_training=False,
    ):
        super().__init__(game_id, parameters, players, game_type, self_training)

        assert len(players) == 1

        self.player = self.players[0]

        # self.player_uid = players[0].user_id
        # self.model_name = players[0].model_name

        self.snake = [(1, 1)]
        self.moves = ["N", "S", "E", "W"]
        self.orient = "E"
        self.apple = (NUM_TILES_PER_SIDE // 4, NUM_TILES_PER_SIDE // 4)

        self.reward = 0

        self.is_game_over = False

    @staticmethod
    def get_game_name():
        return "snake"

    @staticmethod
    def get_num_players():
        return 1

    def get_is_game_over(self):
        return self.is_game_over

    def get_outcome(self, player_sid):
        if not self.is_game_over:
            return None
        return len(self.snake)

    def submit_action(self, action, player_sid=""):
        if action not in self.moves:
            raise PlaygroundInvalidActionException(
                r'Move must be one of "N", "E", "S", or "W"'
            )
        self.orient = action
        self.reward = -0.01  # cost of existence

        if self.snake[-1] == self.apple:
            self.move_snake(True)
            self.apple = (
                random.randint(0, NUM_TILES_PER_SIDE - 1),
                random.randint(0, NUM_TILES_PER_SIDE - 1),
            )
            self.reward = 1
        else:
            self.move_snake()

        if not is_within_screen(self.snake) or not is_not_overlapping(self.snake):
            score = len(self.snake)  # TODO: do something with the score
            self.reward = -1
            self.is_game_over = True
        return True

    def get_state(self, player_sid="", player_id=0):
        state = {
            "player_moving": self.player.user_id,
            "model_name": self.player.model_name,
            "player_moving_id": self.player.player_id,
            "apple": self.apple,
            "snake": self.snake,
        }
        return json.dumps(state), self.reward

    def move_snake(self, grow=False):
        new_snake = self.snake.copy()
        last_x, last_y = new_snake[-1]
        if self.orient == "E":
            new_snake.append((last_x + 1, last_y))
        elif self.orient == "S":
            new_snake.append((last_x, last_y + 1))
        elif self.orient == "W":
            new_snake.append((last_x - 1, last_y))
        elif self.orient == "N":
            new_snake.append((last_x, last_y - 1))
        if not grow:
            new_snake.pop(0)
        self.snake = new_snake

    def get_player_moving(self):
        return self.player
