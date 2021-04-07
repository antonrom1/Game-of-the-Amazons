from src.views.app import AmazkombatApp
from src.controllers.new_game_view_controller import NewGameViewController, NewGameViewControllerDelegate
from src.controllers.game_view_controller import GameViewController
from src.views.game_widget import GameWidgetDelegate, GameWidget
from os import environ


class AppController(NewGameViewControllerDelegate, GameWidgetDelegate):
    def __init__(self):
        self.app = AmazkombatApp()

        self.game_controller = None
        self.new_game_controller = NewGameViewController(self)
        self.app.exec_()


    def new_game_created(self, game):
        self.game_controller = GameViewController(game)
