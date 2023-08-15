from abc import ABC, abstractmethod

import attrs

# If we change from eventlet, we need to change this
from eventlet.green.threading import Timer
from .sid_util import SidSessionInfo
from typing import Dict, List
import time

# How long does the client have to submit an action
# TODO: This should really be configurable
TIMEOUT = 5 * 60  # 5 minutes


class GameParameterInterface:
    """
    Games can optionally define parameters for their games.
    For example, a Go game might want to be able to allow the user to
    specify different board sizes.

    Games can override this class to parameterize their games. These
    parameters are then used in game matching.
    """

    pass


@attrs.define
class PlayerInterface:
    """
    An interface defining information used by a game about its players.
    Games can extend this with subclasses, if they want to define
    more information for each player.
    """

    session_info: SidSessionInfo
    """ Info about socket connection and user """

    player_id: int
    """ Unique ID specifying which player they are in the game """

    def __init__(self, session_info: SidSessionInfo, player_id: int = 0):
        self.session_info = session_info
        self.player_id = player_id

    @property
    def sid(self):
        return self.session_info.sid

    @property
    def user_id(self):
        return self.session_info.user_id

    @property
    def game_id(self):
        return self.session_info.game_id

    @property
    def model_name(self):
        return self.session_info.model_name

    @property
    def is_human(self):
        return self.session_info.is_human


class GameInterface(ABC):
    """
    An abstract class to represent one instance of a running game.
    """

    def __init__(
        self,
        game_id: str,
        parameters: GameParameterInterface,
        players: List[PlayerInterface] = [],
        game_type=0,
        self_training=False,
    ):
        self.parameters = parameters
        self.iteration = 0
        self.game_id = game_id
        # self.players = {player.sid: player for player in players}
        self.players = {player.player_id: player for player in players}
        self.game_type = game_type

        self.reward = 0
        self.timer_thread = None
        self.self_training = self_training
        self.time_last_updated = time.time()

    @abstractmethod
    def submit_action(self, action, player_sid="") -> bool:
        """
        Games define this in their implementations.

        Given an action, which can be an arbitrary socketio-serializable python object,
        and the SID of the player submitting the action, it should update the internal
        state of the game to reflect that action.
        """
        raise NotImplementedError

    # TODO: make this depend on the user_id provided
    @abstractmethod
    def get_state(self, player_sid="", player_id=0):
        """
        Games define this in their implementations.

        Returns an python object, representing the current state of the game.
        For example, chess might return the FEN representation of the board;
        Tic-Tac-Toe might return which squares have X's, and which squares have O's.

        This can be any python-socketio serializable object, but it's often advantageous
        to represent the state as a JSON or a dict.

        player_sid and player_id are the
        """
        raise NotImplementedError

    @abstractmethod
    def get_is_game_over(self) -> bool:
        """
        Games define this in their implementation. Return a
        boolean, indicating if the game is over or not.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_game_name() -> str:
        """
        Defined by subclasses. Returns the name of the game. Should be constant.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_num_players():
        """
        Return the default number of players in the game.
        """
        raise NotImplementedError

    @abstractmethod
    def get_outcome(self, player_id: int) -> float:
        """
        Subclasses implement this. Returns a float representing
        an outcome for Player with player_id, or None if game has not
        ended yet.

        A common heuristic is that 0, 0.5, and 1 are used for loss,
        tie, and win, respectively.
        """
        return None

    @abstractmethod
    def get_player_moving(self) -> PlayerInterface:
        """
        Get the player object of the player who is currently moving.
        """
        raise NotImplementedError

    def get_iteration(self) -> int:
        return self.iteration

    def get_players(self) -> Dict[int, PlayerInterface]:
        """
        Returns a dictionary mapping player_ids to player
        objects.
        """
        return self.players

    def get_game_type(self) -> int:
        """
        Returns a game type, i.e. the pool the game is in.
        0 represents human-only, 1 represents model-only,
        2 represents open.
        """
        return self.game_type

    def reset_timeout(self, callback, callback_args):
        """
        Resets the move timeout, which will call
        callback with callback_args when completed. This generally
        fires when a player has not made a move in TIMEOUT seconds.
        """
        if self.timer_thread is not None:
            self.timer_thread.cancel()
            self.time_last_updated = time.time()

        # Set a timer for the next action
        self.timer_thread = Timer(TIMEOUT, callback, args=callback_args)
        self.timer_thread.start()

    def cancel_timeout(self):
        """
        Stop pending move timeout
        """
        self.timer_thread.cancel()

    @property
    def timeout_timestamp(self) -> int:
        """
        Returns time, in seconds since epoch, when the current pending
        move times out
        """
        return int(self.time_last_updated + TIMEOUT)

    # will call the game-specific function to advance state,
    def advance_game_state(self, action, player_sid="") -> bool:
        """
        Function to internally advance the state of the game
        """
        result = self.submit_action(action, player_sid)
        self.iteration += 1
        return result
