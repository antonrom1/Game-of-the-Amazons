from src.models.amazons import Amazons
from src.views import app, board_view, window, settings
from src.const import PLAYERS, DEFAULT_AI_AI_DELAY

class Game:
    def __init__(self):
        self.app = app.AmazkombatApp()

        self.settings_view = settings.Settings(PLAYERS, self.handle_ai_delay_change, self.is_file_valid)
        self.settings_view.show()

        self.ai_ai_delay = DEFAULT_AI_AI_DELAY
        self.game = None

        self.app.exec_()

    def is_file_valid(self, file):
        try:
            self.game = Amazons(file, self.ai_ai_delay)
        except:
            return False
        else:
            return True

    def handle_ai_delay_change(self, new_val):
        self.ai_ai_delay = new_val
        if self.game is not None:
            self.game.ai_ai_delay = self.ai_ai_delay
