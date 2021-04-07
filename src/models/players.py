"""
Prénom:     Anton
Nom:        ROMANOVA
Matricule:  521935
"""

from abc import ABCMeta, abstractmethod
from src.const import *
from src.models.exceptions import *
from src.models.action import Action
import time
import numpy as np
from src.models.board import EndOfGameStatus
from src.models.pos2d import Pos2D
from functools import lru_cache

import numba

try:
    from src.models.numba_aot import fast_board
except ImportError:
    print("Impossible d'importer les binaires précompilés par numba...")
    from pathlib import Path
    if Path('src/models/numba_aot').is_dir():
        import shutil
        try:
            shutil.rmtree('src/models/numba_aot/__pycache__')  # pour éviter des erreurs d'import par après
        except OSError:
            pass
        print("Probablement la version de python utilisée est différente")
        print("Essayons de compiler... ceci va prendre ~5s et se fera qu'une seule fois")
        try:
            from src.models.numba_aot import fast_board_aot_compiler
            fast_board_aot_compiler.compile()
        except Exception as e:
            print("Une erreur s'est produite lors de la compilation..")
            print(e)
            exit()
        else:
            from src.models.numba_aot import fast_board
            print("Compilation réussie, continuons!")
    else:
        print("Le dossier numba n'a pas été importé")
        exit()


class Player(metaclass=ABCMeta):
    """
    Classe abstraite représentant un joueur quelconque.

    Attributes:
        board (Board): le plateau de jeu sur lequel le joueur va effectuer ses actions
        player_id (int): l'id du joueur
    """

    def __init__(self, board, player_id):
        self.board = board
        self.player_id = player_id

    @abstractmethod
    def _play(self):
        pass

    def play(self):
        """
        Détermine l'action à effectuer et la joue sur le plateau
        """
        action = self._play()
        self.board.act(action)

    @property
    def other_player_id(self):
        """
        int: l'id du joueur adverse
        """
        return PLAYER_2 if self.player_id == PLAYER_1 else PLAYER_1


class HumanPlayer(Player):
    """
    Spécialisation de Player représentant un joueur humain
    """

    def __init__(self, board, player_id):
        super().__init__(board, player_id)

    def _play(self):
        """
        Récupère l'action désirée via stdin

        Returns:
            Action: l'action récupérée sur stdin
        """
        valid = False
        joueur = WHITE if self.player_id == 1 else BLACK

        while not valid:
            coup = input(MESSAGE_COUP.format('1' if self.player_id == PLAYER_1 else '2'))
            if coup.count('>') != 2:
                print(ERREUR_COUP)
                continue
            try:
                action = Action(*coup.split('>'), self.player_id)
                valid = self.board.is_valid_action(action)
            except InvalidActionError:
                continue
        return action

class GameTree:
    """Structure de données représentant un arbre de jeu"""
    def __init__(self, action=None, score=None):
        self.__score = score
        self.__action = action
        self.children = []

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)

    @property
    def score(self):
        """Le score du noeud"""
        return self.__score

    @score.setter
    def score(self, value):
        """Setter du score du noeud"""
        self.__score = value

    @property
    def action(self):
        """L'action du noued"""
        return self.__action

    @action.setter
    def action(self, value):
        """Setter de l'action du noued"""
        self.__action = value

    def __repr__(self):
        return f"Score: {self.score}, action: {self.action}, children: {self.children}"


class AIPlayer(Player):
    """
    Une intelligence artificielle pour le jeu des Amazones utilisant l'algorithme Minimax avec plusieurs améliorations

    MINIMAX:
        L'approfondissement itératif a été implémenté pour que l'IA puisse retourner une action en temps voulu

            Tant qu'il reste du temps (si Timer.timeouts_soon() est à False), minimax à la profondeur suivante est
            appelée.
            L'arbre de jeu déjà évalué est sauvegardé dans la structure GameTree, ce qui permet à Minimax de trier les
            actions afin de traiter les plus favorables avant pour les profondeaurs suivantes afin que le MTDF puisse
            éliminer le plus de branches.

        Le MTDF (Memory-enhanced Test Driver with node n and value f) avec l'élangage alpha-beta
            permet de réduire le le nombre d'actions évalués.
            Dans le but d'accélérer au plus la recherche, une estimation de la fonction économique doit être donnée.
            Ici, l'estimation donnée pour le premier tour est 0, sinon la fonction économique pour l'action précédente.

        Pour minimax, si l'arbre de jeu n'est pas vide (grâce au approfondissement itératif), les actions sont triées
            dans l'ordre décroissant pour pouvoir éliminer le plus de branches grâce au alpha-beta pruning

    FONCTION ÉCONOMIQUE:
        La fonction économique est la combinaison linéaire de plusieurs heuristiques.
        Plus précisément:

        Mobilité:
            la somme de tous les mouvements (pas actions) possibles pour un joueur - celle de l'autre joueur

        Territoire:
            le # de cases qui appartiennent à un joueur - # de cases qui appartiennent à l'autre.
            Une case appartient à un joueur si celui-ci peut l'atteindre en moins de mouvements (Pas actions!)
            que l'autre. Si les deux peuvent l'atteindre en un même # de mouvements, un quart de point sera attribué
            au joueur à qui est le tour.
        Portée:
            Le nombre total de cases que le joueur peut atteindre - le nombre total de cases que l'autre
            joueur peut atteindre. Une case atteignable est une case que le joueur peut atteindre en un nombre
            arbitraire de mouvements avec des mouvements légaux.
        Territoire relatif:
            Lorsqu'une case n'est accessible que par un seul joueur, 4 points sont attribués pour cette case, sinon
            le # de tours nécessaires pour atteindre cette case pour l'autre joueur - ce le # de tours pour ce joueur

    OPTIMISATIONS:
        Dans le but d'accélérer les actions et les fonctions d'évaluation, une classe FastBoard a été crée.
            Cette classe tient en mémoire une matrice numpy de int8 qui représente le plateau.
            Les opérations sur ce plateau sont significativement plus rapides

        La fonction possible_moves et reachability_grid sont évaluées par des fonctions pré-compilées avec Numba

        Également dans le but d'accélérer minimax, la vérification de fin de jeu prématurée ne se fait pas:
            cette vérification demande trop de ressources pour très peu... grâce à la fonction économique, l'IA a
            finalement une très bonne estimation de l'état favorable ou non de jeu.
    """

    def __init__(self, board, player_id, fact=0, timeout=2):
        super().__init__(board, player_id)
        self.t = timeout
        self.timeout = timeout
        self.fact = fact
        self.timer = Timer()
        self.fast_board = FastBoard(board, self.player_id)

        self.last_score = 0  # need that for MTDF

    def _play(self):
        """
        Détermine le meilleur coup à jouer

        Returns:
            Action: le meilleur coup déterminé via minimax
        """
        self.timer = Timer(self.timeout)

        # ~100x plus rapide de mettre le plateau à jour avec les mouvements de history que de le recopier (~10e-5 s)
        self.update_board()

        action, action_np = self.iterative_deepening()

        self.fast_board.act(*action_np, self.player_id)
        return action

    def update_board(self):
        """Met le fast_board à jour avec les actions dans l'historique de self.board"""
        i = -1
        while True:  # dans le cas où l'autre joueur a effectué plusieurs action, on fait un loop
            try:
                last_action = self.board.history[i]
            except IndexError:
                return
            else:
                if last_action.player_id != self.player_id:
                    self.fast_board.act_action(last_action)
                else:
                    return
            i -= 1

    def iterative_deepening(self, max_depth=10):
        """
        L'approfondissement itératif
        args:
            max_depth: int

        return: action, action_np
            Action, tuple(from, to, arrow)
        """

        root = GameTree()
        depth = 1
        action_tuple = None

        while True:
            best_child, remaining_depth = self.MTDF(root, self.last_score, depth)
            self.last_score = best_child.score

            should_go_deeper = not remaining_depth and not self.timer.timeouts_soon() and depth < max_depth

            if best_child.action is not None:
                action_tuple = best_child.action

            if not should_go_deeper:
                break

            depth += 1

        assert action_tuple is not None, "No move found"

        action = self.fast_board.seq_action_to_action(action_tuple, self.player_id)
        return action, action_tuple

    def MTDF(self, root, f, d):
        """
        L'algorithme de MTDF utilisant un null window pour accélérer la recherche de l'arbre de jeu

        root: GameTree
            la racine de l'arbre de jeu
        f: int
            l'approximation du score de la meilleure action

        d: int:
            la profondeur pour minimax
        """
        best_node_depth = 0
        best_node = None

        g = f

        upper_bound = +INF
        lower_bound = -INF

        self.timer._start = time.time()
        while lower_bound < upper_bound and not self.timer.timeouts_soon():
            beta = max(g, lower_bound + 1)
            best_node, best_node_depth = self.minimax(d, root, beta - 1, beta)
            g = best_node.score

            if g < beta:
                upper_bound = g
            else:
                lower_bound = g
            # print(lower_bound, g, upper_bound)

        return best_node, best_node_depth

    def minimax(self, depth, parent_node, alpha=-INF, beta=+INF, maximizing=True) -> (GameTree, int):
        """
        Détermine le coup optimal à jouer selon l'algorithme minimax.

        Args:
            depth (int): la profondeur à explorer dans l'arbre des coups possibles
            maximizing (bool): True si on cherche à maximiser le score et False si on cherche à le minimiser

            alpha: le score minimum pour le joueur dont le score est maximisé
            beta: le score maximum pour le joueur dont le score est minimisé

        Returns:
            Action: le meilleur coup trouvé dans la profondeur explorée
            int: la profondeur restante (e.g. la profondeur maximale est de 10, mais le joueur perd après 3
                coups, la profondeur restante serait 7)

        Additional techniques used:
            - ɑ-β pruning
            - sorting nodes based on depth - 1 results (that we got thanks to iterative deepening).
                this way, we first test the (probably) best results, and we will prune the rest (with ɑ-β)

        """
        best_child = None
        best_score_remaining_depth = depth

        if maximizing:
            best_score = -INF
            player = self.player_id
        else:
            best_score = +INF
            player = self.other_player_id

        winner = self.fast_board.status.winner
        if winner is not None:
            # Il vaut mieux gagner tôt (ou perdre tard) que de gagner tard (ou perdre tôt)
            parent_node.score = WIN + depth
            if winner == self.other_player_id:
                parent_node.score = -parent_node.score
            return parent_node, depth

        if depth == 0:
            parent_node.score = self.objective_function()
            return parent_node, 0

        if not parent_node.children:
            parent_node.children[:] = [GameTree(action) for action in self.fast_board.possible_actions(player)]

        # A sorted list will significantly speed up alpha-beta pruning
        if any(child.score is not None for child in parent_node.children):
            parent_node.children.sort(
                key=lambda child: child.score if child.score is not None else +INF,
                reverse=maximizing
            )

        for child in parent_node.children:
            self.fast_board.act(*child.action, player)

            new_child, remaining_depth = self.minimax(depth - 1, child, alpha, beta, not maximizing)

            score = new_child.score
            child.score = score

            self.fast_board.undo()

            # Si on trouve un meilleur score
            if (score > best_score and maximizing) or (score < best_score and not maximizing):
                best_child = child
                best_score = score
                best_score_remaining_depth = remaining_depth

                # evaluate alpha beta
                if maximizing:
                    alpha = max(alpha, score)
                else:
                    beta = min(beta, score)

                # alpha-beta pruning
                if beta <= alpha:
                    break

            if self.timer.timeouts_soon():
                break

        if best_child is None:
            raise Exception("L'IA n'a pas réussi à trouver d'actions")

        # plus rapide de retourner la 1e meilleure meilleure action que gérer une liste des meilleures actions
        parent_node.score = alpha if player == self.player_id else beta

        # pour que les actions soient triées de manière plus appropriée pour les profondeurs + hautes
        parent_node.score = best_score

        return best_child, best_score_remaining_depth

    def objective_function(self):
        """
        La fonction pour évaluer le plateau
        Renvoie la combinaison linéaire des heuristiques effectuée dans FastBoard
        return: int
        """
        return self.fast_board.heuristics_linear_comb()


class Timer:
    """Simple chronomètre"""
    def __init__(self, time_limit=None):
        self._start = time.time()
        self._end = None
        self._time_limit = time_limit
        self.timeouts_soon_threshold = 0.15

    def stop(self):
        """Arrête le chronomètre"""
        self._end = time.time()

    @property
    def time(self):
        """Renvoie le temps écoulé depuis que le chronomètre a été lancé"""
        end_time = time.time() if self._end is None else self._end
        return end_time - self._start

    @property
    def timed_out(self):
        """Renvoie si le chronomètre va bientot dépasser la limite de temps en utilisant self.timeouts_soon_threshold"""
        try:
            return self._time_limit < self.time
        except TypeError:
            raise ValueError("No time limit defined")

    def timeouts_soon(self):
        try:
            return self._time_limit <= self.time + self.timeouts_soon_threshold
        except TypeError:
            raise ValueError("No time limit defined")


class FastBoard:
    """Classe représentant le plateau de jeu plus rapide que Board"""
    DIRECTIONS = np.array([(i, j) for i in range(-1, 2, 1) for j in range(-1, 2, 1) if not 0 == i == j], dtype=np.int8)

    def __init__(self, board, player):
        self.N = board.N
        self.num_tiles = self.N ** 2

        self.history = []

        self.grid = np.array(board.grid.grid, dtype=np.int8)
        self.queens = [list(map(tuple, np.argwhere(self.grid == q))) for q in (PLAYER_1, PLAYER_2)]
        self.empty_cells = self.grid == EMPTY

        self.player = player
        self.other_player = PLAYER_1 if player == PLAYER_2 else PLAYER_2

        self.moves_cache = np.full((self.N, self.N, self.num_tiles, 2), -1, dtype=np.int8)

    def _clear_cache(self):
        # supprime le cache des pour toutes les méthodes
        self.possible_moves_numba.cache_clear()
        self.possible_actions.cache_clear()
        self.has_moves.cache_clear()
        self.is_current_player_turn.cache_clear()
        self.moves_cache[:] = -1

    @lru_cache
    def is_current_player_turn(self):
        """bool: renovie si c'est au joueur actuel de joueur"""
        if self.history:
            return self.history[-1][-1] == self.other_player  # si il y a déjà eu des tours
        return self.player == PLAYER_1  # si aucun tour n'a été joué, le premier joueur sera le joueur 1

    @property
    def status(self):
        """EndOfGameStatus: renvoie l'état du jeu"""
        scores = []
        for p in (PLAYER_1, PLAYER_2):
            scores.append(self.has_moves(p))
        if all(scores):
            return EndOfGameStatus()
        else:
            return EndOfGameStatus(*map(int, scores))

    def heuristics_linear_comb(self, mobility_coef=2, terr_coef=8, reach_coef=8, relative_terr_coef=2):
        """int: Renvoie la combinaison linéaire des heuristiques"""
        mob = self.mobility()
        terr, reach, relative_terr = self.territory_reachability()

        return mobility_coef * mob + terr_coef * terr + reach_coef * reach + relative_terr_coef * relative_terr

    @staticmethod
    def seq_action_to_action(seq_action, player):
        """
        action_seq: convertit la séquence sous forme ((from_y, from_x), (to_y, to_x), (arr_y, arr_x)) en Action
        player: int: l'id du joueur actuel

        return: Action
        """
        from_pos = Pos2D(*seq_action[0])
        to_pos = Pos2D(*seq_action[1])
        arr_pos = Pos2D(*seq_action[2])
        action = Action(from_pos, to_pos, arr_pos, player)
        return action

    def act(self, from_pos, to_pos, arr_pos, player):
        """
        Effectue l'action donnée
        from_pos: séquence de taille 2
        to_pos: séquence de taille 2
        arr_pos: séquence de taille 2
        player: int: l'id du joueur
        """
        self.history.append((from_pos, to_pos, arr_pos, player))

        self.permutate(from_pos, to_pos)
        self.grid[arr_pos] = ARROW

        # refresh empty cells
        self.empty_cells[from_pos] = True  # mettre from_pos avant arr_pos si jamais arr_pos == from_pos
        self.empty_cells[arr_pos] = False
        self.empty_cells[to_pos] = False

        # refresh queens positions
        self.queens[player][self.queens[player].index(tuple(from_pos))] = to_pos

        self._clear_cache()

    def act_action(self, action):
        """Effectue l'Action action"""
        from_pos = action.old_pos.y, action.old_pos.x
        to_pos = action.new_pos.y, action.new_pos.x
        arr_pos = action.arrow_pos.y, action.arrow_pos.x
        self.act(from_pos, to_pos, arr_pos, action.player_id)

    def _player_reachability(self, player):
        # renvoie la grille représentant le nombre de mouvement que chaque joueur devrait
        # faire afin d'atteindre chaque case
        prev_added = np.empty((self.num_tiles, 2), dtype=np.int8)
        prev_added_idx = len(self.queens[player])
        prev_added[:prev_added_idx] = self.queens[player]
        res = fast_board.reachability_grid(
            self.grid,
            self.N,
            self.DIRECTIONS,
            self.num_tiles,
            self.empty_cells,
            self.moves_cache,
            prev_added,
            prev_added_idx
        )
        return res

    def mobility(self):
        """return: int: le nombre total de mouvements que le joueur peut faire (pas actions!)"""
        mobility_grid = np.zeros_like(self.grid, dtype=np.int8)

        for player in PLAYERS:
            add = 1 if player == self.player else -1
            for queen in self.queens[player]:
                possible_moves = fast_board.possible_moves(self.DIRECTIONS,
                                                           self.N,
                                                           self.num_tiles,
                                                           self.empty_cells,
                                                           np.array(queen, dtype=np.int8),
                                                           self.moves_cache,
                                                           False
                                                           )

                for move in possible_moves:
                    mobility_grid[tuple(move)] += add
        return np.sum(mobility_grid)

    def territory_reachability(self):
        """
        Renvoie la différence entre le nombre de cases qui appartiennent à chaque joueur ainsi que la différence
        entre les cases atteignables.
        Le territoire d'un joueur est défini comme suit:
            Une case appartient à un joueur si il peut atteindre cette case en moins de mouvements
            (sans considérer la phase du tir des flèches), que l'autre joueur.
        Les cases atteignables sont définis tel que une cases atteignable est une cases qu'un joueur peut atteindre
        return: (int, int)
        """
        this_reachability = self._player_reachability(self.player)
        other_reachability = self._player_reachability(self.other_player)

        # si m[i, j] > 0, m[i, j] appartient au joueur actuel, si m[i, j] = 0, aucun, sinon l'autre joueur

        is_curr_player_turn = self.is_current_player_turn()
        territory_grid = self._whos_territory(this_reachability, other_reachability)

        if not is_curr_player_turn:
            territory_grid[territory_grid == 1] = -1

        territory = np.sum(territory_grid) // 4
        reachability = np.count_nonzero(this_reachability) - np.count_nonzero(other_reachability)
        relative_territory = np.sum(self._whos_relative_territory(this_reachability, other_reachability))

        return territory, reachability, relative_territory



    @staticmethod
    @numba.vectorize('int8(int8, int8)', cache=True)
    def _whos_territory(p1_reachability, p2_reachability):
        """
        Renvoie 1 si le territoire appartient à p1, -1 si p2 et 0 si le territoire appartient à personne
        p1_reachability, p2_reachability sont des scalaires (int) et représentent le nombre de mouvement
        que chacun des joueurs
        """
        # on utilise un facteur de 4 car numba.vectorize ne prend pas de constantes et par la suite,
        # un point positif ou neé
        if p1_reachability > p2_reachability > 0 or p2_reachability > p1_reachability == 0:
            return -4
        elif p2_reachability > p1_reachability > 0 or p1_reachability > p2_reachability == 0:
            return 4
        elif p1_reachability == p2_reachability > 0:
            return 1
        return 0

    @staticmethod
    @numba.vectorize('int8(int8, int8)', cache=True)
    def _whos_relative_territory(p1_reachability, p2_reachability):
        """
        Renvoie p2 - p1 si les deux joueurs peuvent atteindre la case, 4 si seulement ce joueur peut, -4 sinon
        """
        if p1_reachability == p2_reachability == 0:
            return 0
        elif p1_reachability > 0 and p2_reachability == 0:
            return 4
        elif p1_reachability == 0 and p2_reachability > 0:
            return -4
        else:
            return p2_reachability - p1_reachability


    def last_moved_queen_influence(self):
        """
        Renvoie le nombre de mouvements possibles de la dernière reine déplacée
        """
        try:
            queen = self.history[-1][0]
        except IndexError:
            return 0
        else:
            possible_moves = fast_board.possible_moves(self.DIRECTIONS,
                                                       self.N,
                                                       self.num_tiles,
                                                       self.empty_cells,
                                                       np.array(queen, dtype=np.int8),
                                                       self.moves_cache,
                                                       False
                                                       )
            return len(possible_moves)

    def mobility_evaluation(self):
        """Renvoie la différence entre le nombre d'actions possibles des reines"""
        return len(self.possible_actions(self.player)) - len(self.possible_actions(self.other_player))

    def permutate(self, pos1, pos2):
        """Permute deux cases du plateau"""
        self.grid[pos1], self.grid[pos2] = self.grid[pos2], self.grid[pos1]

    # def monte_carlo(self, depth):

    def undo(self):
        """Annule la dernière action effectuée"""
        from_pos, to_pos, arr_pos, player = self.history.pop()

        # supprimer la flèche avant de permutter si la flèche est à la position de départ de la reine
        self.grid[arr_pos] = EMPTY
        self.permutate(from_pos, to_pos)

        self.empty_cells[arr_pos] = True
        self.empty_cells[to_pos] = True
        self.empty_cells[from_pos] = False

        self.queens[player][self.queens[player].index(to_pos)] = from_pos

        self._clear_cache()

    @lru_cache
    def has_moves(self, player):
        """Fonction booléenne qui renvoie si le joueur player peut joueur"""
        return len(self.possible_actions(player, return_first_found=True)) > 0

    def __repr__(self):
        res = ''
        for col in self.grid[::-1]:
            for cell in col:
                res += CHARS[cell] + ' '
            res += '\n'
        return res

    @lru_cache
    def possible_moves_numba(self, from_pos, ignore_pos=None, return_first_found=False):
        """Renvoie les mouvements possibles à partir de from_pos"""
        if ignore_pos:
            ignore_pos_np = np.array(ignore_pos, dtype=np.int8)
            res = fast_board.possible_moves_ignore_pos(self.DIRECTIONS,
                                            self.N,
                                            self.num_tiles,
                                            self.empty_cells,
                                            np.array(from_pos, dtype=np.int8),
                                            ignore_pos_np,
                                            return_first_found)
        else:
            res = fast_board.possible_moves(self.DIRECTIONS,
                                             self.N,
                                             self.num_tiles,
                                             self.empty_cells,
                                             np.array(from_pos, dtype=np.int8),
                                             self.moves_cache,
                                             return_first_found)
        res = tuple(map(tuple, res))
        return res

    @lru_cache
    def possible_actions(self, player, return_first_found=False):
        """Renvoie toutes les actions possibles pour un joueur sous forme de liste"""
        actions = []
        for queen in self.queens[player]:
            for queen_move in self.possible_moves_numba(queen):
                for arr_move in self.possible_moves_numba(queen_move, ignore_pos=queen,
                                                          return_first_found=return_first_found):
                    res = (queen, queen_move, arr_move)
                    if return_first_found:
                        return res
                    actions.append(res)
        return actions
