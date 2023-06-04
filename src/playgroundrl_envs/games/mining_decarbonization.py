from ..game_interface import GameInterface, PlayerInterface, GameParameterInterface
import numpy as np
import json
import attrs

class MiningDecarbonizationPlayer(PlayerInterface):
    pass

@attrs.define(frozen = True)
class MiningDecarbonizationParameters(GameParameterInterface):
    pass

WORLD_SIZE = 4


class MiningDecarbonizationGame(GameInterface):
    def __init__(self, game_id, players, game_type, self_training=False):
        super().__init__(game_id, players, game_type, self_training)

        assert(len(players) == 1)
        self.player = self.players[0]

        # initialize the world (true state)
        self._available_resources = np.random.rand(WORLD_SIZE, WORLD_SIZE)
        self._research_invested = np.zeros((WORLD_SIZE, WORLD_SIZE))

        # state observations for current turn
        self.mined_resources = np.zeros((WORLD_SIZE, WORLD_SIZE))
        self.emissions = np.zeros((WORLD_SIZE, WORLD_SIZE))
        # self.money = 1

        self.reward = 0
        self.is_game_over = False

    def submit_action(self, action, player_sid=""):
        action = json.loads(action)
        if "mining" not in action or "exploration" not in action or "research" not in action:
            return False
        mining_budget = np.array(action["mining"], dtype=float)
        explore_budget = np.array(action["exploration"], dtype=float)
        research_budget = np.array(action["research"], dtype=float)
        # softmax over total money
        print(mining_budget.dtype, type(mining_budget.sum()))
        # includes term to prevent divide by 0
        money_allocated = (mining_budget.sum() + explore_budget.sum() + research_budget.sum()) + 0.0001  # * self.money
        mining_budget /= money_allocated
        explore_budget /= money_allocated
        research_budget /= money_allocated
        print(mining_budget, explore_budget, research_budget)

        # TODO: determine the most logical order for this
        # increase available resources based on exploration
        self._available_resources *= (1 + explore_budget)

        # mine based on allocation for mining
        self.mined_resources = self._available_resources * mining_budget
        self._available_resources -= self.mined_resources
        print(self.mined_resources)
        # self.money = self.mined_resources.sum()  # this is the budget for the next turn

        # invest in research and see emissions produced in turn
        self._research_invested += research_budget  # TODO: see if this makes more sense as a product
        # ensure that we cap the amount of research progress we make at 1
        # TODO: emissions should be based on mining budget
        self._research_invested = np.minimum(self._research_invested, np.ones((WORLD_SIZE, WORLD_SIZE)))
        self.emissions = self.mined_resources * (1 - self._research_invested)
        print(self.emissions)

        if self.emissions.sum() == 0:
            self.reward = self.mined_resources.sum()
        else:
            self.reward = self.mined_resources.sum() / self.emissions.sum()

        if self.iteration >= 50:  # end if we get to 2050
            self.is_game_over = True

        return True

    def get_state(self, player_sid="", player_id=0):
        state = {
            "player_moving": self.player.user_id,
            "model_name" : self.player.model_name,
            "player_moving_id" : self.player.player_id,
            'mined_resources' : self.mined_resources.tolist(),
            'emissions' : self.emissions.tolist(),
            "time_step" : self.iteration
        }

        return json.dumps(state), self.reward

    def get_is_game_over(self):
        return self.is_game_over

    @staticmethod
    def get_game_name():
        return "mining decarbonization"

    @staticmethod
    def get_num_players():
        return 1

    def get_outcome(self, player_id):
        if not self.is_game_over:
            return None
        return self.reward

    def get_player_moving(self) -> PlayerInterface:
        return self.player
