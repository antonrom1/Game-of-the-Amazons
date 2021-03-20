from src.views.app import AmazkombatApp
from src.controllers.new_game_view_controller import NewGameViewController, NewGameViewControllerDelegate
from src.controllers.game_view_controller import GameViewController


class AppController(NewGameViewControllerDelegate):
    def __init__(self):
        self.app = AmazkombatApp()

        NewGameViewController(self)
        self.game_controller = None

        self.app.exec_()

    def new_game_created(self, game):
        self.game_controller = GameViewController(game)
