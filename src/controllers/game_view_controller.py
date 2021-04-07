import threading
from src.controllers.player_ui import GuiPlayerDelegate, HumanGuiPlayer
from src.models.amazons import Amazons, AmazonsDelegate
from src.views.board_view import BoardView
from src.views.board_scene import BoardSceneDelegate
from src.views.game_widget import GameWidget, GameWidgetDelegate
from src.controllers.point_pos_bridge import to_ui_coord, action_to_game_coords
from src.controllers.main_thread_executor import MainThreadExecutor
from src.const import QUEEN_ICONS
from copy import deepcopy


class GameViewController(BoardSceneDelegate, GuiPlayerDelegate, AmazonsDelegate, GameWidgetDelegate):
    """
    Gère le lien entre le jeu et l'interface du jeu
    """
    def __init__(self, game: Amazons):
        self.game = game
        self.original_game = deepcopy(self.game)  # to make it possible for the user to restart the game later on

        self.window = None
        self.board_view = None

        self.init_ui()
        self.init_game()
        self.window.show()

        # désactiver le bouton "Recommencer" avant que le premier tour ait été joué
        self.window.restart_game_btn.setDisabled(True)

    def init_game(self):
        """Initialise la partie logique du jeu (model)"""
        self.game.delegate = self
        for player in self.game.players:
            player.delegate = self
            player.board_scene = self.board_view.board_scene

        if not self.game_over():
            game_logic = threading.Thread(target=self.game.play)
            game_logic.daemon = True  # pour que le programme puisse être terminé
            game_logic.start()

    def init_ui(self):
        """Initialise l'interface graphique du jeu"""
        self.init_board_view()
        self.window = GameWidget(self.board_view, self)

    def init_board_view(self):
        """Initialise le BoardView"""
        self.board_view = BoardView(self.game.players[self.game.current_player_idx],
                                    self.game.board.size,
                                    self.window, *self.get_pieces_and_arrows_ui_pos())

    def get_pieces_and_arrows_ui_pos(self):
        """Renvoie les positions des flèches et reines du jeu en position de l'interface graphique"""
        pieces = {}
        for queen, positions in enumerate(self.game.board.queens):
            pieces.update({to_ui_coord(self.game.board.size, pos): queen for pos in positions})

        arrows = [to_ui_coord(self.game.board.size, arr) for arr in self.game.board.arrows]

        return pieces, arrows

    def game_over(self):
        """
        Interdit toute interaction avec le plateau et appelle la méthode GameWidget pour afficher
        le message de fin de jeu
        """
        if self.game.board.status.over:
            MainThreadExecutor.shared.run(self.board_view.board_scene.stop_all_possible_interaction)
            MainThreadExecutor.shared.run(self.window.exhibit_game_over, self.game.board.status.winner)
        return self.game.board.status.over

    # GuiPlayerDelegate protocol

    def played(self, action=None):
        """méthode de GuiPlayerDelegate qui est appelée par GuiPlayer lorsque celui-ci a joué"""
        if not self.window.will_unload:
            if action is not None:
                bd_scene = self.board_view.board_scene
                coords = action_to_game_coords(self.game.board.size, action)
                MainThreadExecutor.shared.run(bd_scene.perform_action, *coords)

    # AmazonsDelegate protocol

    def player_changed(self, new_player_id):
        """méthode de AmazonsDelegate qui est appelée par Amazons lorsque le tour du joueur précédent est terminé"""
        if not self.window.will_unload:
            self.window.update_current_turn_indicator(QUEEN_ICONS[new_player_id])
            new_player = self.game.players[new_player_id]
            self.board_view.board_scene.board_delegate = new_player

        if len(self.game.board.history) > 0:
            MainThreadExecutor.shared.run(self.window.restart_game_btn.setDisabled, False)

    def game_ended(self, winner):
        """méthode de AmazonsDelegate qui est appelée par Amazons lorsque le jeu est fini"""
        if not self.window.will_unload:
            self.game_over()

    # GameWidgetDelegate protocol

    def view_will_unload(self):
        """
        méthode de GameWidgetDelegate qui est appelée par GameWidget lorsque celui-ci est sur le
        point d'être fermé
        La liste de tâche à exécuter sur le main thread est alors vidée
        """
        MainThreadExecutor.shared.main_thread_functions = []

    def restart_game(self):
        """
        méthode de GameWidgetDelegate qui est appelée par GameWidget lorsque le jeu doit être recommencé
        la sauvegarde de game est alors remise dans self.game et le jeu reprend depuis le début
        """
        if not self.window.will_unload:
            # Stop thread execution
            self.game.should_stop_execution = True
            for player in self.game.players:
                player.should_stop_execution = True
                try:
                    player.delegate = None
                except Exception:
                    pass

            # copy the original game state
            self.game = deepcopy(self.original_game)

            self.init_board_view()
            self.window.replace_board_view(self.board_view)
            self.init_game()

            # désactiver le bouton "Recommencer" avant que le premier tour ait été joué
            self.window.restart_game_btn.setDisabled(True)
