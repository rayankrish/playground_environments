import json
import random
from ...game_interface import GameInterface, PlayerInterface, GameParameterInterface
from enum import Enum
from ...sid_util import SidSessionInfo
import attrs

# import enchant


# TODO: Import these from
class Color(str, Enum):
    RED = "RED"
    BLUE = "BLUE"
    ASSASSIN = "ASSASSIN"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"


class PlayerType(str, Enum):
    GIVER = "GIVER"
    GUESSER = "GUESSER"


class CodenamesPlayer(PlayerInterface):
    color: Color
    type: PlayerType


@attrs.define(frozen=True)
class CodenamesParameters(GameParameterInterface):
    num_players: int = 2
    pass


@attrs.define()
class Team:
    giver: CodenamesPlayer
    guesser: CodenamesPlayer


# TODO: Thread safety
# DICTIONARY = enchant.Dict("en_US")

BOARD_SIZE = 5
RED_CARDS = 9
BLUE_CARDS = 8

card_list = None


def get_word_board():
    global card_list
    if card_list is None:
        with open("game_app/games/codenames/wordlist.txt", "r") as f:
            card_list = f.readlines()

    cards = random.sample(card_list, BOARD_SIZE**2)
    cards = [c.strip() for c in cards]
    cards = [cards[i * BOARD_SIZE : (i + 1) * BOARD_SIZE] for i in range(BOARD_SIZE)]
    return cards


def get_card_colors():
    coordinates = random.sample(
        [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE)],
        RED_CARDS + BLUE_CARDS + 1,
    )

    colors = [[Color.INNOCENT for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    # Set
    for i, j in coordinates[:RED_CARDS]:
        colors[i][j] = Color.RED

    for i, j in coordinates[RED_CARDS : RED_CARDS + BLUE_CARDS]:
        colors[i][j] = Color.BLUE

    i, j = coordinates[RED_CARDS + BLUE_CARDS]
    colors[i][j] = Color.ASSASSIN
    return colors


class CodenamesGame(GameInterface):
    def __init__(
        self,
        game_id,
        players,
        game_type,
        parameters: CodenamesParameters,
        self_training=False,
    ):
        super().__init__(game_id, players, game_type, self_training=self_training)

        self.reward = {player.player_id: 0 for player in players}

        self.player_list = players
        self.num_players = parameters.num_players

        assert self.num_players == 4 or self.num_players == 2

        self.players[0].color = Color.RED
        self.players[1].color = Color.RED
        if self.num_players == 4:
            self.players[2].color = Color.BLUE
            self.players[3].color = Color.BLUE

        self.players[0].type = PlayerType.GIVER
        self.players[1].type = PlayerType.GUESSER
        if self.num_players == 4:
            self.players[2].type = PlayerType.GIVER
            self.players[3].type = PlayerType.GUESSER

        # self.teams = {
        #     Color.RED : Team(self.players[0], self.players[1]),
        #     Color.BLUE : Team(self.players[2], self.players[3])
        # }

        self.words = get_word_board()
        self.actual_colors = get_card_colors()
        self.guessed_colors = [
            [Color.UNKNOWN for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
        ]

        self.player_moving_idx = 0

        self.last_clue = ""
        self.last_count = 0
        # Number guessed in a row
        self.guessed_count = 0

        self.winning_team = None

        self.scores = {Color.RED: 0, Color.BLUE: 0}
        self.rewards = {Color.RED: 0, Color.BLUE: 0}

        self.is_game_over = False

    @property
    def player_moving(self):
        return self.players[self.player_moving_idx]

    def increment_turn(self):
        self.player_moving_idx = (self.player_moving_idx + 1) % self.num_players

    def other_team(self, color: Color):
        return color.RED if color == color.BLUE else color.BLUE

    def submit_action(self, action, player_sid=""):
        if self.player_moving.sid != player_sid:
            return False

        # TODO: This isn't necessary
        action = json.loads(action)
        player_color = self.player_moving.color

        if self.player_moving.type == PlayerType.GIVER:
            word = action["word"].lower()
            # if not DICTIONARY.check(word):
            #     print("RECEIVED INVALID WORD -- words must be english")
            #     return False

            # Can't use same word as on board
            for row in self.words:
                for board_word in row:
                    if word == board_word:
                        return False

            count = int(action["count"])

            if count < 0 or count > 9:
                return False

            self.last_clue = word
            self.last_count = count

            self.increment_turn()
        else:
            row, col = action["guess"]
            if row == col == -1:
                # -1, -1 represents finishing your turn
                self.increment_turn()
            else:
                if not 0 <= row < BOARD_SIZE or not 0 <= col < BOARD_SIZE:
                    return False

                if self.guessed_colors[row][col] != Color.UNKNOWN:
                    return False

                color = self.actual_colors[row][col]
                self.guessed_colors[row][col] = color

                if color == Color.ASSASSIN:
                    self.is_game_over = True
                    self.winning_team = self.other_team(self.player_moving.color)
                else:
                    if color != Color.INNOCENT:
                        self.scores[color] += 1

                    if color == player_color:
                        self.guessed_count += 1
                        self.reward[player_color] = 0
                        if self.guessed_count >= self.last_count + 1:
                            self.guessed_count = 0
                            self.increment_turn()

                    elif color == Color.INNOCENT:
                        self.reward[player_color] = 0
                    else:
                        self.reward[player_color] = -1

                    if color != player_color:
                        self.guessed_count = 0
                        self.increment_turn()

                    if self.scores[Color.BLUE] == BLUE_CARDS:
                        self.is_game_over = True
                        self.winning_team = Color.BLUE
                    elif self.scores[Color.RED] == RED_CARDS:
                        self.is_game_over = True
                        self.winning_team = Color.RED

        return True  # Success

    def get_state(self, player_sid="", player_id=-1):
        # TODO: Smarter
        if player_id == -1:
            player_id = 0

        player = self.players[player_id]
        state = {
            "player_moving": self.player_moving.user_id,
            "model_name": self.player_moving.model_name,
            "player_moving_id": self.player_moving.player_id,
            "color": player.color,
            "role": player.type,
            "words": self.words,
            "guessed": self.guessed_colors,
            "actual": self.actual_colors
            if player.type == PlayerType.GIVER
            else self.guessed_colors,
            "clue": self.last_clue,
            "count": self.last_count,
            "scores": self.scores,
        }

        # Reward will be from previous round
        return json.dumps(state), self.reward[player_id]

    @staticmethod
    def get_game_name():
        return "codenames"

    @staticmethod
    def get_num_players():
        return 4

    def get_outcome(self, player_id):
        if not self.is_game_over:
            return None
        player = self.players[player_id]
        return 1 if self.winning_team == player.color else 0

    def get_is_game_over(self):
        return self.is_game_over

    def get_player_moving(self):
        return self.player_moving
