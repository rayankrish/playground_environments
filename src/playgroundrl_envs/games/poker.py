import json
from ..game_interface import GameInterface, PlayerInterface, GameParameterInterface
from enum import Enum
from texasholdem.game.game import TexasHoldEm, GameState
from texasholdem.game.action_type import ActionType
from texasholdem.game.player_state import PlayerState
from texasholdem.card.card import Card
from ..sid_util import SidSessionInfo
import attrs
from ..exceptions import PlaygroundInvalidActionException

BIG_BLIND = 2
SMALL_BLIND = 1
BUY_IN = 200


STR_TO_ACTION_TYPE = {
    "CHECK": ActionType.CHECK,
    "CALL": ActionType.CALL,
    "RAISE": ActionType.RAISE,
    "FOLD": ActionType.FOLD,
}

PLAYER_STATE_TO_STR = {
    PlayerState.SKIP: "SKIP",
    PlayerState.OUT: "OUT",
    PlayerState.IN: "IN",
    PlayerState.TO_CALL: "TO_CALL",
    PlayerState.ALL_IN: "ALL_IN",
}


class PokerPlayer(PlayerInterface):
    pass


@attrs.define(frozen=True)
class PokerParameters(GameParameterInterface):
    num_players: int = 3


class Poker(GameInterface):
    def __init__(
        self,
        game_id,
        players,
        game_type,
        parameters: PokerParameters,
        self_training=False,
    ):
        super().__init__(
            game_id, parameters, players, game_type, self_training=self_training
        )

        self.reward = {player.player_id: 0 for player in players}

        self.player_list = players
        self.num_players = len(self.player_list)

        self.game = TexasHoldEm(BUY_IN, BIG_BLIND, SMALL_BLIND, len(self.players))

        self.last_round_state = None

        self.start_hand()
        self.hand_number = 0

    def start_hand(self):
        self.chips_at_round_start = {}

        for player in self.game.players:
            self.chips_at_round_start[player.player_id] = player.chips
        self.game.start_hand()

    def after_hand_end(self):
        self.hand_number += 1
        self.hands = {}
        # DETERMINE THE HANDS THAT SHOULD BE SHOWN (ONES THAT WERENT FOLDED
        # AND STORE THE CARDS
        for player_id in self.game.in_pot_iter():
            cards = [self._card_to_str(c) for c in self.game.hands[player_id]]
            self.hands[player_id] = cards

        # Determine winnings by player. The API for this is pretty janky, so this is what we're
        # stuck with
        settle_history = self.game.hand_history.settle
        total_winnings = {}
        for pot_id, (
            amount,
            best_rank,
            winners_list,
        ) in settle_history.pot_winners.items():
            winning_per_player = amount / len(winners_list)
            for player_id in winners_list:
                if player_id not in total_winnings:
                    total_winnings[player_id] = 0
                total_winnings[player_id] += winning_per_player

            self.game.pots[pot_id]

        # Determine reward for each player
        reward = {}
        for player_id, player in self.players.items():
            current_chips = self.game.players[player_id].chips
            chips_spent = self.chips_at_round_start[player_id] - current_chips
            # Initialize reward to chip delta for the round
            reward[player_id] = -chips_spent
            self.reward = reward

        self.last_round_state = {"hands": self.hands, "winnings": total_winnings}

        # Start next hand
        self.start_hand()

    def _card_to_str(self, card: Card):
        return Card.INT_SUIT_TO_CHAR_SUIT[card.suit] + str(card.rank + 2).zfill(2)

    def submit_action(self, action, player_sid=""):
        player = self.players[self.game.current_player]

        if player.sid != player_sid:
            raise PlaygroundInvalidActionException("Not your turn")

        action = json.loads(action)
        type = STR_TO_ACTION_TYPE[action["action_type"]]

        try:
            if type == ActionType.RAISE:
                total = action["total"]
                self.game.take_action(type, total=total)
            else:
                self.game.take_action(type)
        except ValueError as e:
            raise PlaygroundInvalidActionException(
                f"Raise must be at least {self.game.min_raise()}."
            )

        # Start next round if necessary
        if not self.game.is_hand_running():
            self.after_hand_end()

        return True  # Success

    def get_state(self, player_sid="", player_id=-1):
        # TODO: Smarter
        if player_id == -1:
            player_id = self.game.current_player

        if self.players[player_id].sid != player_sid:
            raise PlaygroundInvalidActionException("Not player's turn")

        player = self.players[player_id]

        # In game id of player, 0 to player_count -1
        pid = player.player_id

        player_moving_id = self.game.current_player
        player_moving = self.players[player_moving_id]

        # Determine position of current player
        position = -1
        i = 0
        player_count = 0
        for holdem_player in self.game.in_pot_iter(loc=self.game.btn_loc + 1):
            if holdem_player == player.player_id:
                position = i
            i += 1
            player_count += 1

        player_state = self.game.players[pid]
        chips = player_state.chips

        if player_state == PlayerState.OUT:
            chips_bet = 0
            chips_to_call = 0
            pot = self.game.pots[-1]

        else:
            pot = self.game.pots[player_state.last_pot]
            pot_size = pot.get_amount()

            chips_bet = pot.get_player_amount(pid)
            chips_to_call = pot.chips_to_call(pid)

        pot_size = pot.get_amount()
        bet_amount = pot.raised

        # Card format is suit ('s', 'c', 'h', 'd') plus rank (2 - 12)
        if pid not in self.game.hands:
            hole_cards = ["0", "0"]
        else:
            hole_cards = [self._card_to_str(c) for c in self.game.hands[pid]]

        communal_cards = [self._card_to_str(c) for c in self.game.board]

        chip_counts = {}
        amounts_bet = {}
        for cur_player in self.players.values():
            player_chips = self.game.players[cur_player.player_id].chips
            chip_counts[cur_player.player_id] = player_chips

            amounts_bet[cur_player.player_id] = 0
            for pot in self.game.pots:
                amounts_bet[cur_player.player_id] += pot.get_player_amount(
                    cur_player.player_id
                )

        state = {
            # Required paramaters
            "player_moving": player_moving.user_id,
            "model_name": player_moving.model_name,
            "player_moving_id": player_moving.player_id,
            # Global
            "last_round": self.last_round_state,
            "communal_cards": communal_cards,
            "min_raise": self.game.min_raise(),
            "bet_amount": bet_amount,
            "chip_counts": chip_counts,
            "amounts_bet": amounts_bet,
            "user_ids": {
                player.player_id: player.user_id for player in self.players.values()
            },
            "players_left_in_hand": player_count,
            "can_raise": self.game.raise_option,
            "hand_number": self.hand_number,
            # PLayer Specific
            "status": PLAYER_STATE_TO_STR[player_state.state],
            "pot_size": pot_size,
            "chips_to_call": chips_to_call,
            "hole_cards": hole_cards,
            "position": position,
        }

        # Reward will be from previous round
        return json.dumps(state), self.reward[player_id]

    @staticmethod
    def get_game_name():
        return "poker"

    @staticmethod
    def get_num_players():
        return 3

    def get_is_game_over(self):
        return self.game.game_state != GameState.RUNNING

    def get_outcome(self, player_id):
        # TODO: Claim draw
        # I think somehow in the rules a draw is optional
        if self.game.game_state == GameState.RUNNING:
            return None

        if player_id not in self.players:
            return None

        chips = self.game.players[player_id].chips
        return 0 if chips <= 0 else 1

    def get_player_moving(self):
        player_moving_id = self.game.current_player
        player_moving = self.players[player_moving_id]
        return player_moving


if __name__ == "__main__":
    players = [SidSessionInfo(str(i), str(i), True) for i in range(2)]
    cg = Poker(0, players, "poker")

    for i in range(500):
        s, _ = cg.get_state(str(0))
        s = json.loads(s)
        current_sid = s["player_moving"]

        s, reward = cg.get_state(player_sid=current_sid)
        s = json.loads(s)
        print(json.dumps(s, indent=2))
        print("REWARD", reward)

        action = None
        while action not in STR_TO_ACTION_TYPE:
            action = input("ACTION: CHECK CALL RAISE FOLD: \n")
        action_dict = {"action_type": action}
        if action == "RAISE":
            total = int(input("AMOUNT TO RAISE"))
            action_dict["total"] = total

        result = cg.submit_action(json.dumps(action_dict), current_sid)
        if not result:
            print("ACTION FAILED")

        for i in range(2):
            print(cg.get_outcome(str(i)))
