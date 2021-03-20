from src.models.amazons import Amazons
from src.views import app, new_game_settings
from src.const import PLAYERS, AI_AI_DELAY_DEFAULT
from src.models.players import HumanPlayer, AIPlayer
from src.views.strings import HUMAN_PLAYER, AI_PLAYER


class NewGameViewController(new_game_settings.NewGameSettingsDelegate):
    def __init__(self, delegate):
        self.new_game_settings_view = new_game_settings.NewGameSettings(self, PLAYERS)
        self.new_game_settings_view.show()

        self.ai_ai_delay = AI_AI_DELAY_DEFAULT
        self.game = None

        self.delegate = delegate

    def is_board_file_valid(self, file_path) -> bool:
        try:
            Amazons(file_path, self.ai_ai_delay)
            return True
        except:
            return False

    def save_settings(self, file_path, players_str, ai_ai_delay) -> bool:
        try:
            self.game = Amazons(file_path, self.ai_ai_delay)
        except Exception as e:
            return False
        else:
            players = []
            for i, player_str in enumerate(players_str):
                if player_str == HUMAN_PLAYER:
                    cls = HumanPlayer
                elif player_str == AI_PLAYER:
                    cls = AIPlayer
                else:
                    raise ValueError("players_str ne correspondent pas aux types de joueurs définis")
                player = cls(self.game.board, PLAYERS[i])
                players.append(player)
            self.game.players = players
            self.delegate.new_game_created(self.game)
            return True


class NewGameViewControllerDelegate:
    def new_game_created(self, game: Amazons):
        raise NotImplemented
