import threading
from src.controllers.player_ui import GuiPlayerDelegate, HumanGuiPlayer
from src.models.amazons import Amazons, AmazonsDelegate
from src.views.board_view import BoardView
from src.views.board_scene import BoardDelegate
from src.views.window import GameWidget, GameWidgetDelegate
from src.controllers.point_pos_bridge import to_ui_coord, action_to_game_coords
from src.controllers.main_thread_executor import MainThreadExecutor
from copy import deepcopy


class GameViewController(BoardDelegate, GuiPlayerDelegate, AmazonsDelegate, GameWidgetDelegate):
    def __init__(self, game: Amazons):
        self.game = game
        self.original_game = deepcopy(self.game)  # to make it possible for the user to restart the game later on

        self.window = None
        self.board_view = None

        self.init_ui()
        self.init_game()
        self.window.show()

    def init_game(self):
        self.game.delegate = self
        for player in self.game.players:
            player.delegate = self
            player.board_scene = self.board_view.board_scene

        if not self.game_over():
            game_logic = threading.Thread(target=self.game.play)
            game_logic.daemon = True  # pour que le programme puisse être terminé
            game_logic.start()

    def init_ui(self):
        self.init_board_view()
        self.window = GameWidget(self.board_view, self)

        # désactiver le bouton "Recommencer" avant que le premier tour ait été joué
        self.window.restart_game_btn.setDisabled(True)

    def init_board_view(self):

        self.board_view = BoardView(self.game.players[self.game.current_player_idx],
                                    self.game.board.size,
                                    self.window, *self.get_pieces_and_arrows_ui_pos())

    def get_pieces_and_arrows_ui_pos(self):
        pieces = {}
        for queen, positions in enumerate(self.game.board.queens):
            pieces.update({to_ui_coord(self.game.board.size, pos): queen for pos in positions})

        arrows = [to_ui_coord(self.game.board.size, arr) for arr in self.game.board.arrows]

        return pieces, arrows

    def update_view_from_model_data(self):
        self.board_view.board_scene.pieces, self.board_view.board_scene.arrows = self.get_pieces_and_arrows_ui_pos()
        self.board_view.board_scene.redraw_pieces()

    def game_over(self):
        if self.game.board.status.over:
            self.board_view.board_scene.stop_all_possible_interaction()
            self.window.exhibit_game_over(self.game.board.status.winner)
        return self.game.board.status.over

    # GuiPlayerDelegate protocol

    def played(self, action=None):
        self.window.restart_game_btn.setDisabled(False)
        if action is not None:
            bd_scene = self.board_view.board_scene
            coords = action_to_game_coords(self.game.board.size, action)
            MainThreadExecutor.shared.run(bd_scene.perform_action, *coords)

    # AmazonsDelegate protocol

    def player_changed(self, new_player_id):
        # MainThreadExecutor.shared.run(self.update_view_from_model_data)
        new_player = self.game.players[new_player_id]
        self.board_view.board_scene.board_delegate = new_player

    def game_ended(self, winner):
        self.board_view.board_scene.stop_all_possible_interaction()
        MainThreadExecutor.shared.run(self.window.exhibit_game_over, winner)

    # GameWidgetDelegate protocol

    def restart_game(self):
        # Stop thread execution
        self.game.should_stop_execution = True
        for player in self.game.players:
            player.should_stop_execution = True

        # copy the original game state
        self.game = deepcopy(self.original_game)

        self.init_board_view()
        self.window.replace_board_view(self.board_view)
        self.init_game()

        # désactiver le bouton "Recommencer" avant que le premier tour ait été joué
        self.window.restart_game_btn.setDisabled(True)
