import random
from abc import ABCMeta, abstractmethod
from src.const import *
from src.models.exceptions import *
from src.models.action import Action
import time
import numpy as np
from src.models.board import EndOfGameStatus
from src.models.pos2d import Pos2D
from random import shuffle
from numba import njit
from numba.typed import List

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
        self.__children = []

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

    @property
    def children(self):
        return self.__children

    def __repr__(self):
        return f"Score: {self.score}, action: {self.action}, children: {self.children}"


class AIPlayer(Player):
    """
    Spécialisation de la classe Player représentant un joueur utilisant un minimax
    """

    def __init__(self, board, player_id, fact=0, timeout=2, m_m=1, m_t=0.25, m_r=1):
        super().__init__(board, player_id)
        self.t = timeout
        self.timeout = timeout
        self.m_m, self.m_t, self.m_r = m_m, m_t, m_r
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

    def iterative_deepening(self, max_depth=5):

        # ~100x plus rapide de mettre le plateau à jour avec les mouvements de history que de le recopier (~10e-5 s)
        self.update_board()

        depth = 1
        parent_node = MinimaxNode()

        best_move = None

        while True:
            best_child, exited_prematurely = self.minimax(depth, parent_node)

            depth += 1
            should_go_deeper = not exited_prematurely and depth <= max_depth and not self.timer.timeouts_soon()
            if ((not exited_prematurely) or best_move is None) and best_child.action is not None:
                best_move = best_child.action

            if not should_go_deeper:
                break

        print(self.timer.time, best_move, f"depth: {depth - 1}")

        # s'éliminer si le timer a timed out
        assert not self.timer.timed_out and best_move is not None, f"Timed out or no move found {self.timer.time}, {best_move}"

        from_pos, to_pos, arr_pos = [Pos2D(*pos) for pos in best_move]
        action = Action(from_pos, to_pos, arr_pos, self.player_id)
        self.fast_board.act(*best_move, self.player_id)

        return action

    def minimax(self, depth, parent_node, alpha=-INF, beta=+INF, maximizing=True):
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
        exited_prematurely = False

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
            return parent_node, exited_prematurely

        if depth == 0:
            parent_node.score = self.objective_function(player)
            return parent_node, exited_prematurely

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
            score = self.minimax(depth - 1, child, alpha, beta, not maximizing)[0].score
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

                # prune
                if beta <= alpha:
                    break

            if self.timer.timeouts_soon():
                exited_prematurely = True
                break
            # il est plus rapide de retourner la 1e meilleure action que gérer une liste et choisir un nombre aléatoire
        parent_node.score = alpha if player == self.player_id else beta
        if best_child.action is None:
            raise Exception("L'IA n'a pas réussi à trouver d'actions")

        # pour que les actions soient triées de manière plus appropriée pour les profondeurs + hautes
        parent_node.score = best_score
        return best_child, exited_prematurely

    def objective_function(self, curr_player):
        res = self.fast_board.first_order_game_eval()
        # if self.player_id == PLAYER_2:
        #     res += self.fast_board.monte_carlo(16, 1, curr_player) >> 5
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
        self.history = []
        self.N = board.N
        self.grid = np.array(board.grid.grid, dtype=np.uint8)
        self.queens = [list(map(tuple, np.argwhere(self.grid == q))) for q in (PLAYER_1, PLAYER_2)]
        self.empty_cells = self.grid == EMPTY

        self.player = player
        self.other_player = PLAYER_1 if player == PLAYER_2 else PLAYER_2

        self._cached_actions = [None, None]
        self._cached_moves = {}

    def delete_cache(self):
        for p in (PLAYER_1, PLAYER_2):
            self._cached_actions[p] = None
        self._cached_moves = {}

    @property
    def status(self):
        scores = []
        for p in (PLAYER_1, PLAYER_2):
            scores.append(self.has_moves(p))
        if all(scores):
            return EndOfGameStatus()
        else:
            return EndOfGameStatus(*map(int, scores))

    def first_order_game_eval(self):
        terr, reach = self.territory_reachability()
        mobility = self.mobility_evaluation()
        influence = self.last_moved_queen_influence()
        return terr + reach + mobility + influence

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

        self.delete_cache()

    def act_action(self, action):
        from_pos = action.old_pos.y, action.old_pos.x
        to_pos = action.new_pos.y, action.new_pos.x
        arr_pos = action.arrow_pos.y, action.arrow_pos.x
        self.act(from_pos, to_pos, arr_pos, action.player_id)

    def other_player(self, player):
        return PLAYER_1 if player == PLAYER_2 else PLAYER_2

    def monte_carlo(self, samples, to_depth, player):
        evaluation_res = 0
        cache = self._cached_moves, self._cached_actions
        first_depth_actions = self.possible_actions(player)
        for sample in range(samples):
            depth = 0
            while depth < to_depth:
                depth += 1
                curr_player = player if depth % 2 else self.other_player(player)
                if depth == 1:
                    action = random.choice(first_depth_actions)
                else:
                    action = random.choice(self.possible_actions(curr_player))
                self.act(*action, curr_player)
            evaluation_res += self.first_order_game_eval()
            for _ in range(depth):
                self.undo()
        self._cached_moves, self._cached_actions = cache
        return evaluation_res

    def _player_reachability(self, player):
        reachability_grid = np.zeros_like(self.grid, dtype=np.int8)
        prev_added = [*self.queens[player]]
        reachability = 1
        while prev_added:
            new_positions = []
            for from_pos in prev_added:
                for pos in self.possible_moves(from_pos):
                    if reachability_grid[pos] == 0:
                        reachability_grid[pos] = reachability
                        new_positions.append(pos)
            reachability += 1
            prev_added = new_positions
        return reachability_grid

    def territory_reachability(self):
        this_reachability = self._player_reachability(self.player)
        other_reachability = self._player_reachability(self.other_player)

        # si m[i, j] > 0, m[i, j] appartient au joueur actuel, si m[i, j] = 0, aucun, sinon l'autre joueur

        ## TODO: trouver un moyen de dire 1 si this < other et this != 0 ou other == 0 and this != 0 etc.
        # 2 1 0
        # 1 2 0
        # 0 1 0
        # 1 0 0

        def territory_solution(p1, p2):
            if p1 > p2 > 0 or p2 > p1 == 0:
                return -1
            elif p2 > p1 > 0 or p1 > p2 == 0:
                return 1
            return 0

        territory = np.sum(np.fromiter(map(territory_solution, this_reachability.flat, other_reachability.flat), dtype=np.int8))
        reachability = np.count_nonzero(this_reachability) - np.count_nonzero(other_reachability)
        return territory, reachability

    def last_moved_queen_influence(self):
        try:
            queen = self.history[-1][0]
        except IndexError:
            return 0
        else:
            return len(self.possible_moves(queen))

    def mobility_evaluation(self):
        return len(self.possible_actions(self.player)) - len(self.possible_actions(self.other_player))

    def permutate(self, pos1, pos2):
        self.grid[pos1], self.grid[pos2] = self.grid[pos2], self.grid[pos1]

    # def monte_carlo(self, depth):

    def undo(self):
        from_pos, to_pos, arr_pos, player = self.history.pop()

        # supprimer la flèche avant de permutter si la flèche est à la position de départ de la reine
        self.grid[arr_pos] = EMPTY
        self.permutate(from_pos, to_pos)

        self.empty_cells[arr_pos] = True
        self.empty_cells[to_pos] = True
        self.empty_cells[from_pos] = False

        self.queens[player][self.queens[player].index(to_pos)] = from_pos

        self.delete_cache()

    def has_moves(self, player):
        return bool(self.possible_actions(player, return_first_found=True))

    def __repr__(self):
        res = ''
        for col in self.grid[::-1]:
            for cell in col:
                res += CHARS[cell] + ' '
            res += '\n'
        return res

    def possible_moves_numba(self, from_pos, ignore_pos=None, return_first_found=False, cache=True):
        if cache:
            cache_key = from_pos, ignore_pos
            if self._cached_moves.get(cache_key, False):
                return self._cached_moves[cache_key]
        ignore_pos_np = np.array([-1, -1], dtype=np.int8)
        if ignore_pos:
            ignore_pos_np = np.array(ignore_pos, dtype=np.int8)
        res = self._possible_moves_numba(self.DIRECTIONS,
                                   self.N,
                                   self.empty_cells,
                                   np.array(from_pos, dtype=np.int8),
                                   ignore_pos_np,
                                   return_first_found=return_first_found)
        if cache:
            pass # TODO
        return list(map(tuple, res))

    @staticmethod
    @njit()
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

    def possible_moves(self, from_pos, ignore_pos=None, return_first_found=False, cache=True):
        if cache:
            cache_key = from_pos, ignore_pos
            if self._cached_moves.get((cache_key), False):
                return self._cached_moves[cache_key]
        moves = []
        for dx, dy in self.DIRECTIONS:
            i, j = from_pos
            while True:
                i += dy
                j += dx
                if not (0 <= i < self.N and 0 <= j < self.N):
                    break
                if (i, j) == ignore_pos or self.empty_cells[i, j]:
                    moves.append((i, j))
                    if return_first_found:
                        return moves
                else:
                    break
        if cache:
            self._cached_moves[cache_key] = tuple(moves)
        return moves


    def possible_actions(self, player, return_first_found=False):
        if self._cached_actions[player] is not None:
            return self._cached_actions[player]

        actions = []
        for queen in self.queens[player]:
            for queen_move in self.possible_moves(queen):
                for arr_move in self.possible_moves(queen_move, ignore_pos=queen,
                                                    return_first_found=return_first_found):
                    res = (queen, queen_move, arr_move)
                    if return_first_found:
                        return res
                    actions.append(res)
        self._cached_actions[player] = actions
        return actions

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