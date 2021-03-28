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
    LINEAR_COMB_COEFS = 1, 1, 1, 1

    def __init__(self, board, player_id, fact=0, timeout=2):
        super().__init__(board, player_id)
        self.t = timeout
        self.timeout = timeout
        self.fact = fact
        self.timer = Timer()
        self.fast_board = FastBoard(board, self.player_id)

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

        depth = 1
        parent_node = MinimaxNode()

        best_move = None

        while True:
            best_child = self.minimax(depth, parent_node)

            should_go_deeper = not self.timer.timeouts_soon() and depth < max_depth

            if best_child.action is not None:
                best_move = best_child.action

            if not should_go_deeper:
                break

            depth += 1

        print(self.timer.time, best_move, f"depth: {depth}")

        # s'éliminer si le timer a timed out
        assert not self.timer.timed_out and best_move is not None, f"Timed out or no move found {self.timer.time}, {best_move}"

        from_pos, to_pos, arr_pos = [Pos2D(*pos) for pos in best_move]
        action = Action(from_pos, to_pos, arr_pos, self.player_id)
        self.fast_board.act(*best_move, self.player_id)

        return action

    def minimax(self, depth, parent_node, alpha=-INF, beta=+INF, maximizing=True) -> MinimaxNode:
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
            return parent_node

        if depth == 0:
            parent_node.score = self.objective_function()
            return parent_node

        if not parent_node.children:
            parent_node.children[:] = [MinimaxNode(action) for action in self.fast_board.possible_actions(player)]

        assert self.fast_board.has_moves(player)

        # A sorted list will significantly speed up alpha-beta pruning
        if any(child.score is not None for child in parent_node.children):
            parent_node.children.sort(
                key=lambda child: child.score if child.score is not None else +INF,
                reverse=maximizing
            )

        for child in parent_node.children:
            self.fast_board.act(*child.action, player)

            score = self.minimax(depth - 1, child, alpha, beta, not maximizing).score

            child.score = score

            self.fast_board.undo()

            # Si on trouve un meilleur score

            if (score > best_score and maximizing) or (score < best_score and not maximizing):
                best_child = child
                best_score = score

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

        return best_child

    def objective_function(self):
        """La fonction économique pour minimax"""
        res = self.fast_board.heuristics_linear_comb(*self.LINEAR_COMB_COEFS)

        # l'évaluation avec monte carlo demande trop de ressources, elle n'est pas envisageable
        # res += self.fast_board.monte_carlo(16, 1, curr_player) >> 5

        return res


class Timer:
    def __init__(self, time_limit=None):
        self.__start = time.time()
        self.__end = None
        self.__time_limit = time_limit

    def stop(self):
        self.__end = time.time()

    @property
    def time(self):
        end_time = time.time() if self.__end is None else self.__end
        return end_time - self.__start

    @property
    def timed_out(self):
        try:
            return self.__time_limit < self.time
        except TypeError:
            raise ValueError("No time limit defined")

    def timeouts_soon(self, threshold=0.07):
        try:
            return self.__time_limit <= self.time + threshold
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

        self.compile_numba()

    def compile_numba(self):
        """appelle toutes les méthodes jitted (_player_reachability_numba, _possible_moves_numba et whos_territory)"""
        self._player_reachability(self.player)

    def _clear_cache(self):
        self.possible_moves_numba.cache_clear()
        self.possible_actions.cache_clear()
        self.has_moves.cache_clear()

    @property
    def status(self):
        scores = []
        for p in (PLAYER_1, PLAYER_2):
            scores.append(self.has_moves(p))
        if all(scores):
            return EndOfGameStatus()
        else:
            return EndOfGameStatus(*map(int, scores))

    def heuristics_linear_comb(self, terr_coef=1, reach_coef=1, mobility_coef=1, influence_coef=1):
        terr, reach = self.territory_reachability()
        mobility = self.mobility_evaluation()
        influence = self.last_moved_queen_influence()
        res = terr_coef * terr + reach_coef * reach + mobility_coef * mobility + influence_coef * influence
        return res

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

    def other_player(self, player):
        return PLAYER_1 if player == PLAYER_2 else PLAYER_2

    # def _player_reachability(self, player):
    #     reachability_grid = np.zeros_like(self.grid, dtype=np.int8)
    #     prev_added = [*self.queens[player]]
    #     reachability = 1
    #     while prev_added:
    #         new_positions = []
    #         for from_pos in prev_added:
    #             for pos in self.possible_moves_numba(from_pos):
    #                 if reachability_grid[pos] == 0:
    #                     reachability_grid[pos] = reachability
    #                     new_positions.append(pos)
    #         reachability += 1
    #         prev_added = new_positions
    #     return reachability_grid

    def _player_reachability(self, player):
        prev_added = np.zeros((self.num_tiles, 2), dtype=np.int8)
        prev_added_idx = len(self.queens[player])
        prev_added[:prev_added_idx] = self.queens[player]

        return self._player_reachability_numba(self.grid, self.N, self.DIRECTIONS, self.empty_cells,
                                               prev_added, prev_added_idx, self._possible_moves_numba)

    @staticmethod
    @numba.njit(cache=True)
    def _player_reachability_numba(grid, N, DIR, empty_cells, prev_added, prev_added_idx, possible_moves):
        reachability_grid = np.zeros_like(grid, dtype=np.int8)

        reachability = 1

        new_positions = np.zeros_like(prev_added, dtype=np.int8)
        new_positions_idx = 0

        while prev_added_idx != 0:
            for from_pos in prev_added[:prev_added_idx]:
                moves = possible_moves(DIR, N, empty_cells, from_pos)
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

        territory = np.sum(
            self._whos_territory(this_reachability, other_reachability))
        reachability = np.count_nonzero(this_reachability) - np.count_nonzero(other_reachability)
        return territory, reachability

    @staticmethod
    @numba.vectorize('int8(int8, int8)', cache=True)
    def _whos_territory(p1_reachability, p2_reachability):
        """
        Renvoie 1 si le territoire appartient à p1, -1 si p2 et 0 si le territoire appartient à personne
        p1_reachability, p2_reachability sont des scalaires (int) et représentent le nombre de mouvement
        que chacun des joueurs
        """
        if p1_reachability > p2_reachability > 0 or p2_reachability > p1_reachability == 0:
            return -1
        elif p2_reachability > p1_reachability > 0 or p1_reachability > p2_reachability == 0:
            return 1
        return 0

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
                                         self.empty_cells,
                                         np.array(from_pos, dtype=np.int8),
                                         ignore_pos_np,
                                         return_first_found=return_first_found)
        res = tuple(map(tuple, res))
        return res

    @staticmethod
    @numba.njit(cache=True)
    def _possible_moves_numba(DIR,
                              N,
                              empty_cells,
                              from_pos,
                              ignore_pos=np.array([-1, -1], dtype=np.int8),
                              return_first_found: bool = False):
        moves = np.zeros((N ** 2, 2), dtype=np.int8)
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
        return moves[:moves_idx]

    # def possible_moves(self, from_pos, ignore_pos=None, return_first_found=False, cache=True):
    #     if cache:
    #         cache_key = from_pos, ignore_pos
    #         if self._cached_moves.get(cache_key, False):
    #             return self._cached_moves[cache_key]
    #     moves = []
    #     for dx, dy in self.DIRECTIONS:
    #         i, j = from_pos
    #         while True:
    #             i += dy
    #             j += dx
    #             if not (0 <= i < self.N and 0 <= j < self.N):
    #                 break
    #             if (i, j) == ignore_pos or self.empty_cells[i, j]:
    #                 moves.append((i, j))
    #                 if return_first_found:
    #                     return moves
    #             else:
    #                 break
    #     if cache:
    #         self._cached_moves[cache_key] = tuple(moves)
    #     return moves

    # def possible_actions_numba(self, player, return_first_found=False):
    #     if self._cached_actions[player] is not None:
    #         return self._cached_actions[player]
    #
    #     actions

    # def _possible_actions_numba(self, player, return_first_found=False):
    #     pass

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
