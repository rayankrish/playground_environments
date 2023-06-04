import json
from enum import Enum
import sys
from typing import Dict, List

from catanatron.models.map import Water, Port, LandTile
from catanatron.game import Game
from catanatron.models.player import Color
from catanatron.models.enums import RESOURCES, Action, ActionType
from catanatron.state_functions import get_longest_road_length

from catanatron.json import GameEncoder



def longest_roads_by_player(state):
    # Function from them 
    result = dict()
    for color in state.colors:
        result[color.value] = get_longest_road_length(state, color)
    return result



NODE_ID_SEPARATOR = "_"
EDGE_ID_SEPARATOR = ">"

COORD_TO_ID = {
    (2, -2, 0): 0,
    (1, -2, 1): 1,
    (0, -2, 2): 2,
    (2, -1, -1): 3,
    (1, -1, 0): 4,
    (0, -1, 1): 5,
    (-1, -1, 2): 6,
    (2, 0, -2): 7,
    (1, 0, -1): 8,
    (0, 0, 0): 9,
    (-1, 0, 1): 10,
    (-2, 0, 2): 11,
    (1, 1, -2): 12,
    (0, 1, -1): 13,
    (-1, 1, 0): 14,
    (-2, 1, 1): 15,
    (0, 2, -2): 16,
    (-1, 2, -1): 17,
    (-2, 2, 0): 18,
}
ID_TO_COORD = {value: key for key, value in COORD_TO_ID.items()}

    # def new_node_id_from_adj_tiles(adjacent_tiles: List[LandTile]):
    #     """Get a new type of id by concatenating node ids"""

    # def old_node_id_from_new_id(game: Game, new_id: str):
    #     tile_ids = [old_tile_id_from_new_tile_id(id) for id in new_id.split(NODE_ID_SEPARATOR)]
    #     for old_id, adj_list in game.state.board.map.adjacent_tiles.items():
    #         # TODO: Precompute this loop once 
    #         adj_list_ids =  [str(t.id) for t in adj_list]
    #         # TODO: Ordering
    #         if adj_list_ids == tile_ids:
    #             return old_id
class CustomGameEncoder():
    def __init__(self, game: Game):
        self.construct_tile_id_mappings(game)
        self.construct_node_id_mappings(game)

    def construct_tile_id_mappings(self, game: Game):
        print(game.state.board.map.port_nodes)
        self.tile_new_to_old: Dict[str, str] = {}
        self.tile_old_to_new: Dict[str, str] = {}

        for coord, tile in game.state.board.map.land_tiles.items():
            # if type(tile) == Water:
            #     continue
            # if type(tile) == Port:
            #     new_id = tile.id
            # else:
            # TODO: Rayan, some function here 
            # new_id = str(coord[0] + 2) + str(coord[1] + 2) + str(coord[2] + 2)
            new_id = COORD_TO_ID[tuple(coord)]
            old_id = str(tile.id)

            self.tile_new_to_old[new_id] = old_id
            self.tile_old_to_new[old_id] = new_id



    def construct_node_id_mappings(self, game: Game):
        adjacent_tiles = game.state.board.map.adjacent_tiles

        self.node_new_to_old = {}
        self.node_old_to_new = {}

        for old_id, adj_list in adjacent_tiles.items():
            # print("OLD ID", old_id)
            node_ids = sorted([int(self.tile_old_to_new[str(t.id)]) for t in adj_list])
            node_ids = [str(elem) for elem in node_ids]
            new_id = NODE_ID_SEPARATOR.join(node_ids)

            # if new_id not in self.node_new_to_old and old_id not in self.node_old_to_new:
            if new_id in self.node_new_to_old:
                new_id = new_id + '\''
                # print(node_ids, self.node_new_to_old[new_id])
                # new_id
                # old_id
                # 'EXITING'
                # sys.exit()
            self.node_new_to_old[new_id] = old_id
            self.node_old_to_new[old_id] = new_id

        
        print(adjacent_tiles)
        print(len(self.node_old_to_new.keys()))
        print(len(sorted(self.node_new_to_old.values())))
        print(len(self.node_new_to_old))
        # print(self.node_old_to_new.keys())
        # for port_id in game.state.board.map.ports_by_id.keys():
        #     print(port_id)
        #     for node in nodes:
        #         old_node_id = node
        #         new_node_id = str()

        # print(self.node_new_to_old, self.node_old_to_new)


    def old_to_new_edge_id(self, node1: int, node2: int):
        # print('b4', node1, node2)
        node1 = self.node_old_to_new[node1]
        node2 = self.node_old_to_new[node2]
        # print('aft', node1, node2)
        if len(str(node1)) < len(str(node2)):
            return EDGE_ID_SEPARATOR.join(([node1, node2]))
        elif len(str(node1)) > len(str(node2)):
            return EDGE_ID_SEPARATOR.join(([node2, node1]))
        return EDGE_ID_SEPARATOR.join(sorted([node1, node2]))
    
    def new_to_old_edge_id(self, edge_id: str):
        node1, node2 = edge_id.split(EDGE_ID_SEPARATOR)
        node1 = self.node_new_to_old[node1]
        node2 = self.node_new_to_old[node2]

        return tuple(sorted([int(node1), int(node2)]))

    def default(self, obj):
        if obj is None:
            return None
        if isinstance(obj, str):
            return obj
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, tuple):
            return obj
        if isinstance(obj, int):
            return str(obj)
            
        return obj

        
    def convert_state(self, game: Game, player_num):
        if isinstance(game, Game):
            nodes = {}
            edges = {}
            land_tiles = {}

            resources = {}

            # Only do land tiles 
            for coordinate, tile in game.state.board.map.land_tiles.items():
                new_id = self.tile_old_to_new[str(tile.id)]

                land_tiles[new_id] = {
                    'resource':  self.default(tile.resource),
                    'number': self.default(tile.number)
                }

                # Todo - potentially duplicated work 
                for direction, old_node_id in tile.nodes.items():
                    building = game.state.board.buildings.get(old_node_id, None)
                    color = None if building is None else building[0]
                    building_type = None if building is None else building[1]

                    new_node_id = self.node_old_to_new[old_node_id]

                    if building_type is not None:
                        nodes[new_node_id] = {
                            "building": self.default(building_type),
                            "color": self.default(color),
                    }
                        
                for _direction, edge in tile.edges.items():
                    color = game.state.board.roads.get(edge, None)
                    if color == None:
                        continue
                    
                    edge_id = self.old_to_new_edge_id(*edge)

                    edges[edge_id] = {
                        "color": self.default(color),
                    }

            # Remove extraneous player state
            player_state = {}

            for key, val in game.state.player_state.items():
                if key[1] == str(player_num):
                    player_state[key[3: ]] = val


            actions = [self.convert_action(a) for a in game.state.playable_actions]
            
            
            d = {
                "tiles": land_tiles,
                "nodes": nodes,
                "edges": edges,
                # "actions": [self.default(a) for a in game.state.actions],
                "player_state": player_state,
                "colors": [self.default(color) for color in game.state.colors],
                "is_initial_build_phase": game.state.is_initial_build_phase,
                "robber_coordinate": COORD_TO_ID[tuple(game.state.board.robber_coordinate)],
                "current_prompt": self.default(game.state.current_prompt),
                "playable_actions": actions,
                "longest_roads_by_player": longest_roads_by_player(game.state),
                "winning_color": self.default(game.winning_color()),
            }
            return d

    def convert_action(self, action: tuple) -> Dict:
        _, type_, value = action
        # TODO: We can also do additional action conversions to make them more sane
        if type_ in [ActionType.BUILD_SETTLEMENT, ActionType.BUILD_CITY]:
            value = self.node_old_to_new[value]
        if type_ == ActionType.BUILD_ROAD:
            value = self.old_to_new_edge_id(*value)
        if type_ == ActionType.MOVE_ROBBER:
            print(value, type(value))
            color = None if value[1] is None else value[1].value
            value = (COORD_TO_ID[value[0]], color)
        return {
            'type': self.default(type_),
            'value': self.default(value)
        }
    
    def unconvert_action(self, action: Dict, current_color: Color) -> Action:
        """Convert actions back into format recognized by catanatron"""
        type_ = ActionType(action['type'])
        print(type_)
        value = action['value']
        if value == 'None':
            value = None
        if type_ in [ActionType.BUILD_SETTLEMENT, ActionType.BUILD_CITY]:
            value = self.node_new_to_old[value]
        if type_ == ActionType.BUILD_ROAD:
            print(value)
            value = self.new_to_old_edge_id(value)
        if type_ == ActionType.MARITIME_TRADE:
            value = tuple(value)
        if type_ == ActionType.MOVE_ROBBER:
            # value = (tuple(value[0]), None if value[1] is None else Color(value[1]), None)
            value = (ID_TO_COORD[value[0]], None if value[1] is None else Color(value[1]), None)
        print(value, type(value))
        if type(value) == list:
            print("TUPLE CONVERTED")
            value = tuple(value)
        return Action(current_color, type_, value)