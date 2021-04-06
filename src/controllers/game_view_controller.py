import threading
from src.controllers.player_ui import GuiPlayerDelegate, HumanGuiPlayer
from src.models.amazons import Amazons, AmazonsDelegate
from src.views.board_view import BoardView
from src.views.board_scene import BoardDelegate
from src.views.window import GameWidget, GameWidgetDelegate
from src.controllers.point_pos_bridge import to_ui_coord, action_to_game_coords
from src.controllers.main_thread_executor import MainThreadExecutor
from copy import deepcopy



class GameViewController(BoardDelegate, GuiPlayerDelegate):
    def __init__(self, game: Amazons):
        self.game = game
        self.window = None
        self.board_view = None

        self.init_ui()

        self.window.show()

        for player in self.game.players:
            player.delegate = self
            if isinstance(player, HumanGuiPlayer):
                player.board_scene = self.board_view.board_scene

        game_logic = threading.Thread(target=self.game.play)
        game_logic.start()

    def init_ui(self):
        pieces = {}
        for queen, positions in enumerate(self.game.board.queens):
            pieces.update({to_ui_coord(self.game.board.size, pos): queen for pos in positions})

        arrows = [to_ui_coord(self.game.board.size, arr) for arr in self.game.board.arrows]

        self.board_view = BoardView(self.game.players[self.game.current_player_idx],
                                    self.game.board.size,
                                    self.window, pieces, arrows)
        self.window = MainWindow(self.board_view)

    def show_game_over_label_if_needed(self):
        if self.game.board.status.over:
            self.board_view.board_scene.dis

    # GuiPlayerDelegate protocol

    def played(self, action=None):
        if action is not None:
            bd_scene = self.board_view.board_scene
            coords = action_to_game_coords(self.game.board.size, action)
            bd_scene.perform_action(*coords)

    def switch_to_next_player(self, next_player_id):
        self.board_view.board_scene.board_delegate = self.game.players[next_player_id]


def to_ui_coord(board_size, coord):
    return board_size - coord.row - 1, coord.col


def to_game_coord(board_size, coord):
    return Pos2D(board_size - coord[0] - 1, coord[1])


def action_to_game_coords(board_size, action):
    action_coord_list = [action.old_pos, action.new_pos, action.arrow_pos]
    return [to_ui_coord(board_size, coord) for coord in action_coord_list]
