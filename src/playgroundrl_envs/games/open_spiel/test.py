from open_spiel.python import games  # pylint: disable=unused-import
import pyspiel
from open_spiel.python.observation import make_observation

def _escape(x):
  """Returns a newline-free backslash-escaped version of the given string."""
  x = x.replace("\\", R"\\")
  x = x.replace("\n", R"\n")
  return x

def format_shapes(d):
  """Returns a string representing the shapes of a dict of tensors."""
  if len(d) == 1:
    return str(list(d[min(d)].shape))
  else:
    return ", ".join(f"{key}: {list(value.shape)}" for key, value in d.items())

def add_line(line):
    print(line)

def _format_params(d, as_game=False):
  """Format a collection of params."""

  def fmt(val):
    if isinstance(val, dict):
      return _format_params(val, as_game=True)
    else:
      return _escape(str(val))

  if as_game:
    return d["name"] + "(" + ",".join(
        "{}={}".format(key, fmt(value))
        for key, value in sorted(d.items())
        if key != "name") + ")"
  else:
    return "{" + ",".join(
        "{}={}".format(key, fmt(value))
        for key, value in sorted(d.items())) + "}"

def print_game_type_debug(game, game_type):

    observation_params = (
       None
    )
    default_observation = make_observation(
        game,
        imperfect_information_observation_type=None,
        params=observation_params,
    )

    infostate_observation = make_observation(
        game, pyspiel.IIGObservationType(perfect_recall=True)
    )

    public_observation = None
    private_observation = None

    # Instantiate factored observations only for imperfect information games,
    # as it would yield unncessarily redundant information for perfect info games.
    # The default observation is the same as the public observation, while private
    # observations are always empty.
    if game_type.information == game_type.Information.IMPERFECT_INFORMATION:
        public_observation = make_observation(
            game,
            pyspiel.IIGObservationType(
                public_info=True,
                perfect_recall=False,
                private_info=pyspiel.PrivateInfoType.NONE,
            ),
        )
        private_observation = make_observation(
            game,
            pyspiel.IIGObservationType(
                public_info=False,
                perfect_recall=False,
                private_info=pyspiel.PrivateInfoType.SINGLE_PLAYER,
            ),
        )

    add_line("")
    add_line("GameType.chance_mode = {}".format(game_type.chance_mode))
    add_line("GameType.dynamics = {}".format(game_type.dynamics))
    add_line("GameType.information = {}".format(game_type.information))
    add_line("GameType.long_name = {}".format('"{}"'.format(game_type.long_name)))
    add_line("GameType.max_num_players = {}".format(game_type.max_num_players))
    add_line("GameType.min_num_players = {}".format(game_type.min_num_players))
    add_line("GameType.parameter_specification = {}".format("[{}]".format(
        ", ".join('"{}"'.format(param)
                    for param in sorted(game_type.parameter_specification)))))
    add_line("GameType.provides_information_state_string = {}".format(
        game_type.provides_information_state_string))
    add_line("GameType.provides_information_state_tensor = {}".format(
        game_type.provides_information_state_tensor))
    add_line("GameType.provides_observation_string = {}".format(
        game_type.provides_observation_string))
    add_line("GameType.provides_observation_tensor = {}".format(
        game_type.provides_observation_tensor))
    add_line("GameType.provides_factored_observation_string = {}".format(
        game_type.provides_factored_observation_string))
    add_line("GameType.reward_model = {}".format(game_type.reward_model))
    add_line("GameType.short_name = {}".format('"{}"'.format(
        game_type.short_name)))
    add_line("GameType.utility = {}".format(game_type.utility))

    add_line("")
    add_line("NumDistinctActions() = {}".format(game.num_distinct_actions()))
    add_line("PolicyTensorShape() = {}".format(game.policy_tensor_shape()))
    add_line("MaxChanceOutcomes() = {}".format(game.max_chance_outcomes()))
    add_line("GetParameters() = {}".format(_format_params(game.get_parameters())))
    add_line("NumPlayers() = {}".format(game.num_players()))
    add_line("MinUtility() = {:.5}".format(game.min_utility()))
    add_line("MaxUtility() = {:.5}".format(game.max_utility()))
    add_line("UtilitySum() = {}".format(game.utility_sum()))
    add_line("MaxGameLength() = {}".format(game.max_game_length()))
    add_line('ToString() = "{}"'.format(str(game)))

    if infostate_observation and infostate_observation.tensor is not None:
        add_line("InformationStateTensorShape() = {}".format(
            format_shapes(infostate_observation.dict)))
        add_line("InformationStateTensorLayout() = {}".format(
            game.information_state_tensor_layout()))
        add_line("InformationStateTensorSize() = {}".format(
            len(infostate_observation.tensor)))
    if default_observation and default_observation.tensor is not None:
        add_line("ObservationTensorShape() = {}".format(
            format_shapes(default_observation.dict)))
        add_line("ObservationTensorLayout() = {}".format(
            game.observation_tensor_layout()))
        add_line("ObservationTensorSize() = {}".format(
            len(default_observation.tensor)))

def main():
    games_list = pyspiel.registered_games()
    print("Registered games:")
    print(games_list)

    for game_instance in games_list:
        print("------------------------------------------")
        print("Game:", game_instance.short_name)

        try:
            game = pyspiel.load_game(game_instance.short_name)
            print("New game:", game)

            game_type = game.get_type()

            print("Game Type:", game_type)

            print_game_type_debug(game, game_type)
            print("")
        except Exception as e:
            print("Error:", e)
            print("")


if __name__ == "__main__":
    main()