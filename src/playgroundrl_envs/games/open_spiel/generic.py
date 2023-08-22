import json
import pyspiel

class OpenSpielGame:
    def __init__(self, game_name):
        self.game_name = game_name
        game = pyspiel.load_game(game_name)
        self.state = game.new_initial_state()
        self.num_players = game.num_players()
        self.players = list(range(self.num_players))
        self.is_game_over = False

    def submit_action(self, action, player_id):
        if player_id not in self.players:
            raise ValueError("Invalid player ID")

        if self.state.current_player() != player_id:
            raise ValueError("Not your turn")

        try:
            action = self.state.string_to_action(self.state.current_player(), action)
            self.state.apply_action(action)
        except pyspiel.SpielError:
            raise ValueError("Invalid move")

        self.is_game_over = self.state.is_terminal()

    def get_is_game_over(self):
        return self.is_game_over

    def get_state(self, player_id):
        if player_id not in self.players:
            raise ValueError("Invalid player ID")

        state = {
            "fen": self.state.observation_string(player_id),
            "observation": self.state.observation_tensor(player_id),
            "player_moving": self.state.current_player(),
        }
        reward = 0.0  # TODO: specify reward
        return json.dumps(state), reward

    def get_game_name(self):
        return self.game_name

    def get_num_players(self):
        return self.num_players

    def get_player_moving(self):
        return self.state.current_player()

    def get_outcome(self, player_id):
        if self.is_game_over:
            returns = self.state.returns()
            if player_id in self.players:
                return returns[player_id]
            return 0.0

if __name__ == "__main__":
    # Example usage
    game = OpenSpielGame(game_name="tic_tac_toe")

    # Suppose it's player 0's turn and they make a move
    game.submit_action("x(0,0)", player_id=0)

    # Get the current state for player 0
    state_json, reward = game.get_state(player_id=0)
    print("State:", state_json)
    print("Reward:", reward)

    # Check if the game is over
    print("Game Over:", game.get_is_game_over())

    # Get the player currently moving
    print("Player Moving:", game.get_player_moving())

    # Get the outcome for player 0
    outcome = game.get_outcome(player_id=0)
    print("Outcome for Player 0:", outcome)
