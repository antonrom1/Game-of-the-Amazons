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
        if self.game_controller is None:
            self.game_controller = GameViewController(game)
            self.game_controller.window.add_delegate(self)
            self.new_game_controller = None

    def create_new_game(self):
        assert isinstance(self.game_controller.window, GameWidget)
        self.new_game_controller = NewGameViewController(self)

        self.game_controller.window.close()
        self.game_controller = None
