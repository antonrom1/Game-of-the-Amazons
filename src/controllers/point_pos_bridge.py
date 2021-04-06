from src.models.pos2d import Pos2D

def to_ui_coord(board_size, coord):
    return board_size - coord.row - 1, coord.col


def to_game_coord(board_size, coord):
    return Pos2D(board_size - coord[0] - 1, coord[1])


def action_to_game_coords(board_size, action):
    action_coord_list = [action.old_pos, action.new_pos, action.arrow_pos]
    return [to_ui_coord(board_size, coord) for coord in action_coord_list]
