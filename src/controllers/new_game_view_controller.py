"""
Prénom:     Anton
Nom:        ROMANOVA
Matricule:  521935
"""

from src.models.amazons import Amazons
from src.views.new_game_settings import NewGameSettings, NewGameSettingsDelegate
from src.const import PLAYERS, AI_AI_DELAY_DEFAULT_MILLIS
from src.controllers.player_ui import HumanGuiPlayer, AIGuiPlayer
from src.views.const_strings import HUMAN_PLAYER, AI_PLAYER


class NewGameSettingsViewController(NewGameSettingsDelegate):
    """Supervise la création d'un nouveau jeu avec NewGameSettingsView"""
    def __init__(self, delegate):
        self.new_game_settings_view = NewGameSettings(self, PLAYERS)
        self.new_game_settings_view.show()

        self.ai_ai_delay = AI_AI_DELAY_DEFAULT_MILLIS
        self.game = None

        self.delegate = delegate

    def is_board_file_valid(self, file_path) -> bool:
        """
        Renvoie si le fichier donnée est un fichier valide

        la vérification se fait en initialisant le jeu. Si une erreur a lieu, le fichier est pas bien défini
        """
        try:
            Amazons(file_path, self.ai_ai_delay)
            return True
        except:
            return False

    def save_settings(self, file_path, players_str, ai_ai_delay) -> bool:
        """
        Crée une instance de Amazons et l'envoie aux observateurs (ici le AppController) si il est bon et renvoie
        un bool, si oui ou non le jeu a pu être crée
        """
        try:
            self.game = Amazons(file_path, show_text_board=False)
        except Exception:
            # le fichier plateau n'est pas correctement défini
            return False
        else:
            players = []
            ai_ai_delay = ai_ai_delay if all(player == AI_PLAYER for player in players_str) else 0
            for i, player_str in enumerate(players_str):
                if player_str == HUMAN_PLAYER:
                    player = HumanGuiPlayer(self.game.board, PLAYERS[i])
                elif player_str == AI_PLAYER:
                    player = AIGuiPlayer(ai_ai_delay, self.game.board, PLAYERS[i])
                else:
                    raise ValueError("players_str ne correspondent pas aux types de joueurs définis")
                players.append(player)
            self.game.players = players
            self.delegate.new_game_created(self.game)
            return True


class NewGameViewControllerDelegate:
    """Protocole d'observateur de NewGameSettingsViewController"""
    def new_game_created(self, game: Amazons):
        """Est appelé lorsqu'un nouveau jeu est crée"""
        pass
