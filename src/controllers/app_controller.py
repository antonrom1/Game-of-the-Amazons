"""
Prénom:     Anton
Nom:        ROMANOVA
Matricule:  521935
"""

from src.views.app import AmazkombatApp
from src.controllers.new_game_view_controller import NewGameSettingsViewController, NewGameViewControllerDelegate
from src.controllers.game_view_controller import GameViewController
from src.views.game_widget import GameWidgetDelegate, GameWidget
from os import environ


class AppController(NewGameViewControllerDelegate, GameWidgetDelegate):
    """
    Gère le lien entre la fenêtre de création de jeu et la fenêtre de jeu
    """
    def __init__(self):
        self.app = AmazkombatApp()

        self.game_controller = None
        self.new_game_controller = NewGameSettingsViewController(self)
        self.app.exec_()

    # NewGameViewControllerDelegate

    def new_game_created(self, game):
        """
        méthode de NewGameViewControllerDelegate qui est appelée par NewGameSettingsViewController lorsque l'utilisateur
        crée un nouveau jeu
        """
        if self.game_controller is None:
            self.game_controller = GameViewController(game)
            self.game_controller.window.add_delegate(self)
            self.new_game_controller = None

    # GameWidgetDelegate

    def create_new_game(self):
        """
        méthode de GameWidgetDelegate qui est appelée par GameWidget lorsque l'utilisateur
        demande de créer un nouveau jeu
        """
        assert isinstance(self.game_controller.window, GameWidget)
        self.new_game_controller = NewGameSettingsViewController(self)

        self.game_controller.window.close()
        self.game_controller = None
