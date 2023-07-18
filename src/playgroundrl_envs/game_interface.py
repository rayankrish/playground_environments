from abc import ABC, abstractmethod

import attrs

# If we change from eventlet, we need to change this
from eventlet.green.threading import Timer
from .sid_util import SidSessionInfo
from typing import List
import time

# How long does the client have to submit an action
# TODO: This should really be configurable
TIMEOUT = 5 * 60  # 5 minutes


class GameParameterInterface:
    pass


@attrs.define
class PlayerInterface:
    session_info: SidSessionInfo
    player_id: int

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
    def __init__(
        self,
        game_id,
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

    @property
    def timeout_timestamp(self) -> int:
        """
        Returns time, in seconds since epoch, when the current pending
        move times out
        """
        return int(self.time_last_updated + TIMEOUT)

    # will call the game-specific function to advance state,
    def advance_game_state(self, action, player_sid=""):
        result = self.submit_action(action, player_sid)
        self.iteration += 1
        return result

    @abstractmethod
    def submit_action(self, action, player_sid=""):
        return True

    # TODO: make this depend on the user_id provided
    @abstractmethod
    def get_state(self, player_sid="", player_id=0):
        return None

    @abstractmethod
    def get_is_game_over(self):
        """
        Abstract, so inheritors don't forget
        to implement it
        """
        pass

    @staticmethod
    @abstractmethod
    def get_game_name():
        return ""

    @staticmethod
    @abstractmethod
    def get_num_players():
        return 0

    @abstractmethod
    def get_outcome(self, player_id):
        return None

    def get_iteration(self):
        return self.iteration

    def get_players(self):
        return self.players

    def get_game_type(self):
        return self.game_type

    def reset_timeout(self, callback, callback_args):
        if self.timer_thread is not None:
            self.timer_thread.cancel()
            self.time_last_updated = time.time()

        # Set a timer for the next action
        self.timer_thread = Timer(TIMEOUT, callback, args=callback_args)
        self.timer_thread.start()

    @abstractmethod
    def get_player_moving(self) -> PlayerInterface:
        pass

    def cancel_timeout(self):
        self.timer_thread.cancel()
