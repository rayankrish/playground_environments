from datetime import datetime, timedelta


class SidSessionInfo:
    def __init__(self, sid, user_id, is_human):
        self.sid = sid
        self.user_id = user_id
        self.game_id = ""
        self.model_name = ""
        self.is_human = is_human
        # Time to wait before creation
        self.wait_time = 0
        self.creation = datetime.now()
        """Time player joined queue"""
        self.model_type = None

    def join_new_game(self, game_id, model_name):
        self.game_id = game_id
        self.model_name = model_name

    def leave_game(self):
        self.game_id = ""
        self.model_name = ""

    def get_model_name(self):
        return self.model_name

    def get_user_id(self):
        return self.user_id
