import random
from abc import ABCMeta, abstractmethod
from src.const import *
from src.models.exceptions import *
from src.models.action import Action
import time
import numpy as np
from src.models.board import EndOfGameStatus
from src.models.pos2d import Pos2D
from enum import Enum
from functools import lru_cache

import numba


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


class MinimaxNode:
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
        return self.__score

    @score.setter
    def score(self, value):
        self.__score = value

    @property
    def action(self):
        return self.__action

    @action.setter
    def action(self, value):
        self.__action = value

    def __repr__(self):
        return f"Score: {self.score}, action: {self.action}, children: {self.children}"


class AIPlayer(Player):
    """
    Spécialisation de la classe Player représentant un joueur utilisant un minimax
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
        return self.iterative_deepening()

    def update_board(self):
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

        # ~100x plus rapide de mettre le plateau à jour avec les mouvements de history que de le recopier (~10e-5 s)
        self.update_board()
        root = MinimaxNode()

        depth = 1

        best_move = None

        while True:
            best_child, remaining_depth = self.MTDF(root, self.last_score, depth)
            self.last_score = best_child.score

            should_go_deeper = not remaining_depth and not self.timer.timeouts_soon() and depth < max_depth

            if best_child.action is not None:
                best_move = best_child.action

            if not should_go_deeper:
                break

            depth += 1

        print(self.timer.time, best_move, f"depth: {depth}")

        # s'éliminer si le timer a timed out
        assert not self.timer.timed_out and best_move is not None, f"Timed out or no move found {self.timer.time}, {best_move}"


        action = self.fast_board.np_to_action(best_move, self.player_id)

        self.fast_board.act(*best_move, self.player_id)

        try:
            self.scores.append(best_child.scores)
        except AttributeError:
            pass

        print(best_child.score)
        return action

    def MTDF(self, root, f, d):
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

    def minimax(self, depth, parent_node, alpha=-INF, beta=+INF, maximizing=True) -> (MinimaxNode, int):
        """
        Détermine le coup optimal à jouer selon l'algorithme minimax.

        Args:
            depth (int): la profondeur à explorer dans l'arbre des coups possibles
            maximizing (bool): True si on cherche à maximiser le score et False si on cherche à le minimiser

            alpha: le score minimum pour le joueur dont le score est maximisé
            beta: le score maximum pour le joueur dont le score est minimisé

        Returns:
            Action: le meilleur coup trouvé dans la profondeur explorée

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
            parent_node.score = self.fast_board.heuristics_linear_comb()
            return parent_node, 0

        if not parent_node.children:
            parent_node.children[:] = [MinimaxNode(action) for action in self.fast_board.possible_actions(player)]

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


class Timer:
    def __init__(self, time_limit=None):
        self._start = time.time()
        self._end = None
        self._time_limit = time_limit

    def stop(self):
        self._end = time.time()

    @property
    def time(self):
        end_time = time.time() if self._end is None else self._end
        return end_time - self._start

    @property
    def timed_out(self):
        try:
            return self._time_limit < self.time
        except TypeError:
            raise ValueError("No time limit defined")

    def timeouts_soon(self, threshold=0.07):
        try:
            return self._time_limit <= self.time + threshold
        except TypeError:
            raise ValueError("No time limit defined")


class FastBoard:
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

        self.compile_numba()

    def compile_numba(self):
        """appelle toutes les méthodes jitted (_player_reachability_numba, _possible_moves_numba et whos_territory)"""
        try:
            self.possible_moves_numba(self.queens[0][0])
        except IndexError:
            return
        self._player_reachability(self.player)

    def _clear_cache(self):
        self.possible_moves_numba.cache_clear()
        self.possible_actions.cache_clear()
        self.has_moves.cache_clear()
        self.is_current_player_turn.cache_clear()
        self.moves_cache[:] = -1

    @lru_cache
    def is_current_player_turn(self):
        if self.history:
            return self.history[-1][-1] == self.other_player  # si il y a déjà eu des tours
        return self.player == PLAYER_1  # si aucun tour n'a été joué, le premier joueur sera le joueur 1

    @property
    def status(self):
        scores = []
        for p in (PLAYER_1, PLAYER_2):
            scores.append(self.has_moves(p))
        if all(scores):
            return EndOfGameStatus()
        else:
            return EndOfGameStatus(*map(int, scores))

    def heuristics_linear_comb(self, mobility_coef=2, terr_coef=8, reach_coef=1, relative_terr_coef=2, blocked_queens_coef=3):

        mob = self.mobility()
        blocked_queens = self.blocked_queens()
        terr, reach, relative_terr = self.territory_reachability()

        return mobility_coef * mob + terr_coef * terr + reach_coef * reach + \
               relative_terr_coef * relative_terr + blocked_queens_coef * blocked_queens

    @staticmethod
    def np_to_action(np_action, player):
        from_pos = Pos2D(*np_action[0])
        to_pos = Pos2D(*np_action[1])
        arr_pos = Pos2D(*np_action[2])
        action = Action(from_pos, to_pos, arr_pos, player)
        return action


    def filled_ratio(self):
        return np.count_nonzero(self.empty_cells) / self.num_tiles

    def act(self, from_pos, to_pos, arr_pos, player):
        self.history.append((from_pos, to_pos, arr_pos, player))

        self.permutate(from_pos, to_pos)
        self.grid[arr_pos] = ARROW

        # refresh empty cells
        self.empty_cells[from_pos] = True  # mettre from_pos avant arr_pos si jamais arr_pos == from_pos
        self.empty_cells[arr_pos] = False
        self.empty_cells[to_pos] = False

        # refresh queens positions
        self.queens[player][self.queens[player].index(from_pos)] = to_pos

        self._clear_cache()

    def act_action(self, action):
        from_pos = action.old_pos.y, action.old_pos.x
        to_pos = action.new_pos.y, action.new_pos.x
        arr_pos = action.arrow_pos.y, action.arrow_pos.x
        self.act(from_pos, to_pos, arr_pos, action.player_id)

    def _player_reachability(self, player):
        prev_added = np.empty((self.num_tiles, 2), dtype=np.int8)
        prev_added_idx = len(self.queens[player])
        prev_added[:prev_added_idx] = self.queens[player]
        res = self._player_reachability_numba(
            self.grid,
            self.N,
            self.DIRECTIONS,
            self.num_tiles,
            self.empty_cells,
            self.moves_cache,
            prev_added,
            prev_added_idx,
            self._possible_moves_numba
        )
        return res

    def blocked_queens(self):
        blocked_queens_eval = 0
        for player in PLAYERS:
            add = -1 if player == self.player else 1
            for queen in self.queens[player]:
                possible_moves = self._possible_moves_numba(self.DIRECTIONS,
                                                            self.N,
                                                            self.num_tiles,
                                                            self.empty_cells,
                                                            np.array(queen, dtype=np.int8),
                                                            self.moves_cache)

                if len(possible_moves) == 0:
                    blocked_queens_eval += add
        return blocked_queens_eval

    def mobility(self):
        mobility_grid = np.zeros_like(self.grid, dtype=np.int8)

        for player in PLAYERS:
            add = 1 if player == self.player else -1
            for queen in self.queens[player]:
                possible_moves = self._possible_moves_numba(self.DIRECTIONS,
                                                            self.N,
                                                            self.num_tiles,
                                                            self.empty_cells,
                                                            np.array(queen, dtype=np.int8),
                                                            self.moves_cache)

                for move in possible_moves:
                    mobility_grid[tuple(move)] += add
        return np.sum(mobility_grid)



    @staticmethod
    @numba.njit(cache=True)
    def _player_reachability_numba(grid, N, DIR, num_tiles, empty_cells, moves_cache, prev_added, prev_added_idx, possible_moves):
        reachability_grid = np.zeros_like(grid, dtype=np.int8)

        reachability = 1

        new_positions = np.empty_like(prev_added, dtype=np.int8)
        new_positions_idx = 0

        while prev_added_idx != 0:
            for from_pos in prev_added[:prev_added_idx]:
                moves = possible_moves(DIR, N, num_tiles, empty_cells, from_pos, moves_cache)
                for pos_i, pos_j in moves:
                    if reachability_grid[pos_i, pos_j] == 0:
                        reachability_grid[pos_i, pos_j] = reachability
                        new_positions[new_positions_idx] = pos_i, pos_j
                        new_positions_idx += 1
            reachability += 1
            prev_added[:new_positions_idx] = new_positions[:new_positions_idx]
            prev_added_idx = new_positions_idx
            new_positions_idx = 0
        return reachability_grid

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
            return len(self.possible_moves_numba(queen))

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
        return bool(self.possible_actions(player, return_first_found=True))

    def __repr__(self):
        res = ''
        for col in self.grid[::-1]:
            for cell in col:
                res += CHARS[cell] + ' '
            res += '\n'
        return res

    @lru_cache
    def possible_moves_numba(self, from_pos, ignore_pos=None, return_first_found=False):
        """Renvoie les mouvements possibles d'un"""
        ignore_pos_np = np.array([-1, -1], dtype=np.int8)
        if ignore_pos:
            ignore_pos_np = np.array(ignore_pos, dtype=np.int8)
        res = self._possible_moves_numba(self.DIRECTIONS,
                                         self.N,
                                         self.num_tiles,
                                         self.empty_cells,
                                         np.array(from_pos, dtype=np.int8),
                                         self.moves_cache,
                                         ignore_pos_np,
                                         return_first_found=return_first_found)
        res = tuple(map(tuple, res))
        return res

    @staticmethod
    @numba.njit(cache=True)
    def _possible_moves_numba(DIR,
                              N,
                              num_tiles,
                              empty_cells,
                              from_pos,
                              cache,
                              ignore_pos=np.array([-1, -1], dtype=np.int8),
                              return_first_found: bool = False):

        if ignore_pos[0] == -1 and cache[from_pos[0], from_pos[1], 0, 0] != -1:
            cached_res = cache[from_pos[0], from_pos[1]]
            until_idx = np.argmax(cached_res[:, 0] == -1)
            return cache[from_pos[0], from_pos[1], :until_idx]

        moves = np.empty((num_tiles, 2), dtype=np.int8)
        moves_idx = 0
        for d in DIR:
            # i, j = from_pos
            curr_pos = np.copy(from_pos)
            while True:
                curr_pos += d
                if not (0 <= curr_pos[0] < N and 0 <= curr_pos[1] < N):
                    break
                # print(self.empty_cells[i, j])
                if np.all(curr_pos == ignore_pos) or empty_cells[curr_pos[0], curr_pos[1]]:
                    if return_first_found:
                        return curr_pos.reshape(1, 2)
                    moves[moves_idx] = curr_pos
                    moves_idx += 1
                else:
                    break
        final_moves = moves[:moves_idx]
        if not return_first_found and ignore_pos[0] == -1:
            cache[from_pos[0], from_pos[1], :moves_idx] = final_moves
        return final_moves

    @lru_cache
    def possible_actions(self, player, return_first_found=False):
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


class GameStage(Enum):
    Opening = 0  # première phase de jeu
    MiddleGame = 1  # commence lorsque 25% du plateau est rempli
    EndGame = 2  # commence lorsque chaque carré ne peut être atteint que par un seul joueur


if __name__ == "__main__":
    from src.models.board import Board
    from src.models.amazons import Amazons
    from time import time

    g = Amazons('/Users/anton/Desktop/partie4/ressources/boards/plateau_3.txt')
    print('Initializing board')
    board = FastBoard(g.board, PLAYER_2)
    init_pos = board.queens[0][0]
    init_pos_np = np.array(init_pos, dtype=np.int8)
    board.possible_moves_numba(init_pos_np, cache=False)

    start = time()
    for _ in range(50000):
        board.possible_moves(init_pos, cache=False)
    print(time() - start)

    start = time()
    for _ in range(50000):
        board.possible_moves_numba(init_pos_np, cache=False)
    print(time() - start)
@numba.vectorize('int8(int8, int8)', cache=True)
def _whos_relative_territory(p1_reachability, p2_reachability):
    if p1_reachability == p2_reachability == 0:
        return 0
    elif p1_reachability > 0 and p2_reachability == 0:
        return 4
    elif p1_reachability == 0 and p2_reachability > 0:
        return -4
    else:
        return p2_reachability - p1_reachability

