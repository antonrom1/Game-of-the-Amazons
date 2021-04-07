"""
Prénom:     Anton
Nom:        ROMANOVA
Matricule:  521935
"""

from src.controllers.point_pos_bridge import to_game_coord, to_ui_coord
from src.models.action import Action
from src.models.players import Player, AIPlayer
from src.views.board_scene import BoardSceneDelegate
from time import time


class GuiPlayer(Player):
    """
    Classe représentant un joueur de l'interface graphique
    """
    def __init__(self, board, player_id):
        super(GuiPlayer, self).__init__(board, player_id)
        self.board_scene = None
        self.action = None
        self.delegate = None
        self.can_act = False

        self.should_stop_execution = False

    def play(self):
        """Si l'exécution du thread doit être arrêté, aucune action ne sera jouée"""
        action = self._play()
        if not self.should_stop_execution:
            self.board.act(action)


class HumanGuiPlayer(GuiPlayer, BoardSceneDelegate):
    """
    Classe représentant un joueur humain jouant avec une interface graphique
    """
    def __init__(self, board, player_id):
        super(HumanGuiPlayer, self).__init__(board, player_id)
        self.action = None

    def _play(self):
        """Attend que le joueur humain ait joué son coup"""
        self.can_act = True
        self.action = None
        self.board_scene.allow_pieces_interaction(self.player_id)

        # wait until the user moves his pieces
        while self.action is None and not self.should_stop_execution:
            pass
        self.can_act = False
        try:
            self.delegate.played()
        except AttributeError:
            pass

        return self.action

    # BoardSceneDelegate

    def piece_selected(self, coord) -> [tuple]:
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.
        Renvoie les cases de destination possibles pour la reine donnée
        """
        queen_coord = to_game_coord(self.board.size, coord)
        moves = list(self.board._possible_moves_from(queen_coord))
        return [to_ui_coord(self.board.size, m) for m in moves]

    def piece_moved(self, from_coord, to_coord) -> [tuple]:
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.

        Renvoie les cases de destination possibles pour une flèche d'une reine venant de from_coord qui
        s'est déplacée en to_coord
        """
        queen_init_coords = to_game_coord(self.board.size, from_coord)
        queen_final_coord = to_game_coord(self.board.size, to_coord)

        possible_arr_positions = list(self.board._possible_moves_from(queen_final_coord, queen_init_coords))

        return [to_ui_coord(self.board.size, pos) for pos in possible_arr_positions]

    def is_action_valid(self, queen_from, queen_to, arr) -> bool:
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.

        Renvoie si l'action est valide
        """
        if not self.can_act:
            return False
        queen_from_bd = to_game_coord(self.board.size, queen_from)
        queen_to_bd = to_game_coord(self.board.size, queen_to)
        arr_bd = to_game_coord(self.board.size, arr)

        try:
            player = self.board.grid[queen_from_bd]
        except IndexError:
            print("Invalid queen position")
            return False

        try:
            action = Action(queen_from_bd, queen_to_bd, arr_bd, player)
        except Exception:
            print("This is not an action")
            return False

        try:
            self.board.act(action)
        except Exception:
            print("Action is invalid")
            return False
        else:
            # l'action est valide!
            self.board.undo()

            return True

    def perform_action(self, queen_from, queen_to, arr):
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.

        Effectue l'action donnée
        """
        self.action = Action(*[to_game_coord(self.board.size, pos)
                               for pos in (queen_from, queen_to, arr)], self.player_id)


class AIGuiPlayer(GuiPlayer, AIPlayer, BoardSceneDelegate):
    """Classe représentant un joueur IA jouant avec à travers une interface graphique"""
    def __init__(self, ai_ai_delay, *args, **kwargs):
        super(AIGuiPlayer, self).__init__(*args, **kwargs)
        self.ai_ai_delay = ai_ai_delay
        self.action_start_time = None

        self.can_return_action = False

    def _play(self):
        """
        Appelle AIGuiPlayer pour avoir l'action de l'IA et attend que l'action soit appliquée sur la GUI avant
        de la renvoyer
        """
        self.action_start_time = time()
        self.board_scene.stop_all_possible_interaction()
        action = super(AIGuiPlayer, self)._play()
        self.can_return_action = False

        while not (time() - self.action_start_time >= self.ai_ai_delay or
                   self.should_stop_execution):
            pass
        try:
            self.delegate.played(action)
        except AttributeError:
            pass
        while not (self.can_return_action or self.should_stop_execution):
            pass
        return action

    def piece_selected(self, coord) -> [tuple]:
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.

        Ne renvoie rien car toutes les actions de l'IA sont effectuées par l'IA
        """
        return []

    def piece_moved(self, from_coord, to_coord) -> [tuple]:
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.

        Ne renvoie rien car toutes les actions de l'IA sont effectuées par l'IA
        """
        return []

    def is_action_valid(self, queen_from, queen_to, arr) -> bool:
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.

        Renvoie True car toutes les actions de l'IA sont effectuées par l'IA
        """
        return True

    def perform_action(self, queen_from, queen_to, arr):
        """
        méthode de BoardSceneDelegate qui est appelée par BoardScene.

        La GUI a effectué l'action, mettre can_return_action à True pour pouvoir retourner l'action
        """
        # attendre que la gui ait fini l'animation avant d'appliquer le coup à Amazons
        self.can_return_action = True


class GuiPlayerDelegate:
    """Protocole d'observateur d'un GUI Player"""
    def played(self, action):
        """Est appelé lorsqu'une action a été jouée"""
        raise NotImplemented
