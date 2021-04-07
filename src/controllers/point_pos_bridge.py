from src.models.pos2d import Pos2D

def to_ui_coord(board_size, coord):
    """Renvoie la coordonnée coord en coordonnée pour la GUI"""
    return board_size - coord.row - 1, coord.col


def to_game_coord(board_size, coord):
    """Renvoie la coordonnée coord pour GUI en coordonnée pour le jeu"""
    return Pos2D(board_size - coord[0] - 1, coord[1])


def action_to_game_coords(board_size, action):
    """Convertit une action action en coordonnées pour l'interface graphique"""
    action_coord_list = [action.old_pos, action.new_pos, action.arrow_pos]
    return [to_ui_coord(board_size, coord) for coord in action_coord_list]
