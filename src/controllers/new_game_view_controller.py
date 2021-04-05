from src.models.amazons import Amazons
from src.views import new_game_settings
from src.const import PLAYERS, AI_AI_DELAY_DEFAULT
from src.models.players import AIPlayer
from src.controllers.game_view_controller import HumanGuiPlayer, AIGuiPlayer
from src.views.const_strings import HUMAN_PLAYER, AI_PLAYER
from abc import ABC, abstractmethod


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
        except Exception:
            # le fichier plateau n'est pas correctement défini
            return False
        else:
            players = []
            for i, player_str in enumerate(players_str):
                if player_str == HUMAN_PLAYER:
                    cls = HumanGuiPlayer
                elif player_str == AI_PLAYER:
                    cls = AIGuiPlayer
                else:
                    raise ValueError("players_str ne correspondent pas aux types de joueurs définis")
                player = cls(self.game.board, PLAYERS[i])
                players.append(player)
            self.game.players = players
            self.delegate.new_game_created(self.game)
            return True


class NewGameViewControllerDelegate(ABC):
    @abstractmethod
    def new_game_created(self, game: Amazons):
        pass
