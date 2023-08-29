import unittest
from playgroundrl_envs.games.codenames.codenames import (
    CodenamesPlayer,
    CodenamesGame,
    CodenamesParameters,
)

from playgroundrl_envs.sid_util import SidSessionInfo
import json, random


def create_default_game():
    params = CodenamesParameters()

    session_info1 = SidSessionInfo(
        sid="sid-0",
        user_id=0,
        is_human=False,
    )

    session_info2 = SidSessionInfo(
        sid="sid-1",
        user_id=1,
        is_human=False,
    )

    players = [
        CodenamesPlayer(
            player_id=0,
            session_info=session_info1,
        ),
        CodenamesPlayer(
            player_id=1,
            session_info=session_info2,
        ),
    ]

    game = CodenamesGame(
        game_id=0,
        parameters=params,
        players=players,
        game_type=0,
    )

    return game

def giver_valid_move(game):
    state = json.loads(game.get_state()[0])  
    return "valid", json.dumps({
        "word": "xenophobic",  # random irrelevant word
        "count": random.randint(1, 9),
    })

def giver_invalid_move(game):
    state = json.loads(game.get_state()[0])  
    error = random.randint(1, 3)
    
    word = "xenophobic"
    count = random.randint(1, 9)

    if error == 1: # invalid word
        word = random.choice(state["words"])
    elif error == 2: # invalid count
        count = -10 + random.randint(0, 1) * random.random()
    elif error == 3: # invalid word and count
        word = random.choice(state["words"])
        count = -10 + random.randint(0, 1) * random.random()

    return "invalid", json.dumps({
        "word": word,
        "count": count,
    })


def guesser_valid_move(game):
    state = json.loads(game.get_state()[0])  
    
    valid_words = []
    for idx in range(len(state["words"])):
        if state["guessed"][idx] != "UNKNOWN" or state["actual"][idx] != "RED":
            continue
        valid_words.append(idx)
    
    print("valid words: ", valid_words)
    guess_num = random.randint(1, min(4, len(valid_words)))

    return "valid", json.dumps({
        "guesses": random.sample(valid_words, guess_num),
    })

def guesser_invalid_move(game):
    state = json.loads(game.get_state()[0])  

    valid_words = []
    non_ours_words = []
    guessed_words = []
    assassin_word = None

    for idx in range(len(state["words"])):
        if state["guessed"][idx] != "UNKNOWN":
            guessed_words.append(idx)

        if state["actual"][idx] != "RED" and state["guessed"][idx] == "UNKNOWN":
            non_ours_words.append(idx)

        if state["guessed"][idx] == "UNKNOWN" and state["actual"][idx] == "RED":
            valid_words.append(idx)

        if state["actual"][idx] == "ASSASSIN":
            assassin_word = idx

    error = random.randint(1, 5)

    valid_padding = random.sample(valid_words, min(random.randint(1, 3), len(valid_words)))

    # split valid words into two groups
    valid_words1 = random.sample(valid_padding, random.randint(0, max(0, len(valid_padding) - 1)))
    valid_words2 = [x for x in valid_padding if x not in valid_words1]
    
    if len(guessed_words) == 0 or len(non_ours_words) == 0:
        error = random.randint(2, 4)

    if error == 1:  # guessed word
        return "invalid", json.dumps({
            "guesses": valid_words1 + [random.choice(guessed_words)] + valid_words2,
        })
    elif error == 2:  # non-valid word
        return "invalid", json.dumps({
            "guesses": valid_words1 + [random.random()] + valid_words2,
        })
    elif error == 3:  # non-valid word
        return "invalid", json.dumps({
            "guesses": valid_words1 + [-10] + valid_words2,
        })
    elif error == 4:  # assassin word
        
        print(state)
        print(assassin_word)
        print(valid_words1 + [assassin_word] + valid_words2)
    
        return "assassin", json.dumps({
            "guesses": valid_words1 + [assassin_word] + valid_words2,
        })
    elif error == 5:  # non-ours word
        return "not-ours", json.dumps({
            "guesses": valid_words1 + [random.choice(non_ours_words)] + valid_words2,
        })

class TestCodenamesDefinition(unittest.TestCase):

    def test_random_game(self):

        num_epochs = 100

        for i in range(num_epochs):
            game = create_default_game()

            while not game.get_is_game_over():
                state = json.loads(game.get_state()[0])
                player = state["player_moving"]
                if player == 0:
                    do_invalid = random.random() < 0.5
                    while do_invalid:
                        status, move = giver_invalid_move(game)
                        with self.assertRaises(Exception):
                            game.submit_action(move, "sid-0")
                        do_invalid = random.random() < 0.5
                    status, move = giver_valid_move(game)
                    game.submit_action(move, "sid-0")
                else:
                    do_invalid = random.random() < 0.5
                    end_turn = False
                    while do_invalid:
                        status, move = guesser_invalid_move(game)
                        if status != "assassin" and status != "not-ours":
                            with self.assertRaises(Exception):
                                game.submit_action(move, "sid-1")
                        elif status == "assassin":
                            game.submit_action(move, "sid-1")
                            print("Winning", game.winning_team)
                            self.assertTrue(game.get_is_game_over())
                            end_turn = True
                            break
                        elif status == "not-ours":
                            game.submit_action(move, "sid-1")
                            end_turn = True
                            break
                        do_invalid = random.random() < 0.5

                    if end_turn:
                        continue

                    status, move = guesser_valid_move(game)
                    game.submit_action(move, "sid-1")            


if __name__ == "__main__":
    unittest.main()
