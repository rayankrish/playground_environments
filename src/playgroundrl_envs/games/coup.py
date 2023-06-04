from ..game_interface import GameInterface


class CoupGame(GameInterface):
    def submit_action(self, action, player_sid=""):
        pass

    def get_state(self, player_sid=""):
        pass

    @staticmethod
    def get_game_name():
        return "coup"

    @staticmethod
    def get_num_players():
        return 5

    def get_outcome(self, player_sid):
        pass

    def __init__(self, game_id, players, game_type):
        super().__init__(game_id, players, game_type)
        self.game_id = game_id

