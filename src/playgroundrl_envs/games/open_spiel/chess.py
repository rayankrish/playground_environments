import json
import pyspiel
from .generic import OpenSpielGame

class ChessGame(OpenSpielGame):
    def __init__(self):
        super().__init__("chess")
    
if __name__=="__main__":
    # Example usage
    chess_game = ChessGame()

    # Suppose it's player 0's turn and they make a move
    chess_game.submit_action("e4", player_id=1)

    # Get the current state for player 0
    state_json, reward = chess_game.get_state(player_id=0)
    print("State:", state_json)
    print("Reward:", reward)

    # Check if the game is over
    print("Game Over:", chess_game.get_is_game_over())

    # Get the player currently moving
    print("Player Moving:", chess_game.get_player_moving())

    # Get the outcome for player 0
    outcome = chess_game.get_outcome(player_id=0)
    print("Outcome for Player 0:", outcome)
