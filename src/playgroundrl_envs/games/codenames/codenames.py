import json
import random
from ...game_interface import GameInterface, PlayerInterface, GameParameterInterface
from enum import Enum
import attrs
from importlib.resources import files
from typing import List, Dict, Any
from ...exceptions import PlaygroundInvalidActionException

from nltk.corpus import wordnet as word_corpus_loader
import nltk

try:
    word_corpus_loader.ensure_loaded()
except:
    nltk.download("wordnet")

# Just store corpus as a shared global variable for now
# Important it's global, becausae we don't want a new
# corpus per game
word_corpus = set(word_corpus_loader.words())


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


@attrs.define
class CodenamesPlayer(PlayerInterface):
    color: Color = None
    type: PlayerType = None


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

BOARD_SIZE = 25
RED_CARDS = 9
BLUE_CARDS = 8

card_list = None


def get_word_board():
    global card_list
    if card_list is None:
        card_list = (
            files(package="playgroundrl_envs.games.codenames")
            .joinpath("wordlist.txt")
            .read_text()
        ).split("\n")

    cards = random.sample(card_list, BOARD_SIZE)
    cards = [c.strip() for c in cards]
    return cards


def get_card_colors():
    coordinates = list(range(BOARD_SIZE))
    random.shuffle(coordinates)

    colors = [Color.INNOCENT for _ in range(BOARD_SIZE)]

    # Set
    for i in coordinates[:RED_CARDS]:
        colors[i] = Color.RED

    for i in coordinates[RED_CARDS : RED_CARDS + BLUE_CARDS]:
        colors[i] = Color.BLUE

    i = coordinates[RED_CARDS + BLUE_CARDS]
    colors[i] = Color.ASSASSIN
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
        super().__init__(
            game_id, parameters, players, game_type, self_training=self_training
        )

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

        self.words = get_word_board()
        self.actual_colors = get_card_colors()
        self.guessed_colors = [Color.UNKNOWN] * BOARD_SIZE
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
    def player_moving(self) -> CodenamesPlayer:
        return self.players[self.player_moving_idx]

    def increment_turn(self) -> None:
        self.guessed_count = 0
        self.player_moving_idx = (self.player_moving_idx + 1) % self.num_players

    def other_team(self, color: Color) -> bool:
        return color.RED if color == color.BLUE else color.BLUE

    def validate_guesses(self, guesses: List[int]) -> None:
        seen = set()
        for guess in guesses:
            if type(guess) != int:
                raise PlaygroundInvalidActionException("Guess was not an integer")

            if not -1 <= guess < BOARD_SIZE:
                # Guess out of range
                raise PlaygroundInvalidActionException(
                    f"Guess out not in range (-1, {BOARD_SIZE})"
                )

            if self.guessed_colors[guess] != Color.UNKNOWN:
                # Guessed an already guessed square
                raise PlaygroundInvalidActionException(
                    "Guessed a previously-guessed card"
                )

            if guess in seen:
                # Duplicate guess in list
                raise PlaygroundInvalidActionException("Duplicate guesses in list")
            seen.add(guess)

    def handle_guesser_action(self, action: Dict[str, Any]) -> bool:
        """
        Logic if we received action for guesser
        """
        end_turn_automatically = False
        player_color = self.player_moving.color

        if "guess" in action:
            # Single-guess mode
            guesses = [action["guess"]]
        elif "guesses" in action:
            # Multi-guess mode
            end_turn_automatically = True
            guesses = action["guesses"]
        else:
            # Requires one of guess or guesses
            return PlaygroundInvalidActionException(
                "User must specify one of 'guess' or 'guesses' in socket request."
            )

        self.validate_guesses(guesses)

        # RESET REWARD
        self.reward[player_color] = 0
        for guess_idx, guess in enumerate(guesses):
            if guess == -1:
                # -1, -1 represents finishing your turn
                self.increment_turn()
                break
            else:
                color = self.actual_colors[guess]
                # Update to signify it has been guessed
                self.guessed_colors[guess] = color

                if color == Color.ASSASSIN:
                    self.is_game_over = True
                    self.winning_team = self.other_team(self.player_moving.color)
                    self.increment_turn()
                    break
                else:
                    if color != Color.INNOCENT:
                        # Increase score for a team
                        self.scores[color] += 1

                    if color == player_color:
                        self.guessed_count += 1
                        self.reward[player_color] += 1

                        if self.guessed_count >= self.last_count + 1:
                            # We've guessed more than the count given
                            self.increment_turn()
                            break
                        else:
                            keep_guessing = True

                    elif color == Color.INNOCENT:
                        # Penalty for an innocent is -0.5
                        self.reward[player_color] -= 0.5
                    else:
                        # Penalty for opposing team is -1
                        self.reward[player_color] -= 1

                    if color != player_color:
                        # If we didn't guess correct,
                        # it's the other team's turn
                        self.guessed_count = 0
                        self.increment_turn()
                        break

                    # Check for game over conditions
                    if self.scores[Color.BLUE] == BLUE_CARDS:
                        self.is_game_over = True
                        self.winning_team = Color.BLUE

                    elif self.scores[Color.RED] == RED_CARDS:
                        self.is_game_over = True
                        self.winning_team = Color.RED

            if guess_idx == len(guesses) - 1 and end_turn_automatically:
                # If we've already exhausted the guesses given to us,
                # we should go to the next turn automatically
                self.increment_turn()
                break

        return True

    def handle_giver_action(self, action: Dict[str, Any]) -> bool:
        """
        Logic if we received action for spymaster player
        """
        if "word" not in action or "count" not in action:
            raise PlaygroundInvalidActionException(
                'Socket message must be in format \{"word": str, "count": int \}'
            )

        word = action["word"].lower().strip()

        if " " in word:
            raise PlaygroundInvalidActionException("Clue must be only a single word")

        if not word.isalpha():
            raise PlaygroundInvalidActionException("Word must consist of only letters")

        if not word in word_corpus:
            raise PlaygroundInvalidActionException(
                "Word not recognized (must belong to NLTK corpus)"
            )

        # Can't use same word as on board
        for board_word in self.words:
            # Check if either is a substring of the other
            if board_word in word or word in board_word:
                raise PlaygroundInvalidActionException(
                    "Word cannot be a substring or superstring of any board word."
                )

        count = int(action["count"])

        if count < 0 or count > 9:
            raise PlaygroundInvalidActionException("Count must be between 0 and 9")

        self.last_clue = word
        self.last_count = count

        self.increment_turn()
        return True

    def submit_action(self, action, player_sid=""):
        """
        Callback to handle action
        """
        if self.player_moving.sid != player_sid:
            raise PlaygroundInvalidActionException("Not your turn.")

        # TODO: This isn't necessary
        action = json.loads(action)

        if self.player_moving.type == PlayerType.GIVER:
            return self.handle_giver_action(action)
        else:
            return self.handle_guesser_action(action)

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
