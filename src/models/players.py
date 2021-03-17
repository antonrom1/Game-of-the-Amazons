import random
from abc import ABCMeta, abstractmethod
from src.const import *
from src.models.exceptions import *
from src.models.action import Action
import time
import src.models.matrix as matrix
from copy import deepcopy


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

    def _play(self):
        """
        Détermine le meilleur coup à jouer

        Returns:
            Action: le meilleur coup déterminé via minimax
        """
        return self.iterative_deepening(timeout=self.timeout)

    def iterative_deepening(self, max_depth=15, timeout=2):

        timer = Timer(timeout)
        depth = 1
        parent_node = MinimaxNode()
        best_move = None
        while True:
            minimax_timer = Timer()

            best_child, exited_prematurely = self.minimax(depth, parent_node, timer)
            minimax_exec_time = minimax_timer.time

            depth += 1
            should_go_deeper = not exited_prematurely and depth <= max_depth and not timer.timeouts_soon()
            if should_go_deeper:
                # essaye d'estimer le temps d'exécution pour le minimax de profondeur n + 1
                # le temps peut être estimé à la racine carrée du facteur de branchement
                # grâce aux optimisations comme ɑ-β pruning, triage, ...
                remaining_time = timeout - timer.time
                # should_go_deeper = self.branching_factor() ** 0.5 * minimax_exec_time < remaining_time

            if (not exited_prematurely) or best_move is None:
                best_move = best_child.action

            if not should_go_deeper:
                break

        assert not timer.timed_out and best_move is not None, f"Timed out or no move found {timer.time}, {best_move}"
        print(f"Found a move with depth {depth - 1}: {best_child.action, best_child.score}")
        return best_move

    def minimax(self, depth, parent_node, timer, alpha=-INF, beta=+INF, maximizing=True):
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

        if depth == 0:
            parent_node.score = self.objective_function(curr_player=player)
            return parent_node, exited_prematurely

        winner = self.board.status.winner
        if winner is not None:
            # Il vaut mieux gagner tôt (ou perdre tard) que de gagner tard (ou perdre tôt)
            parent_node.score = WIN + depth
            if winner == self.other_player_id:
                parent_node.score = -parent_node.score
            return parent_node, exited_prematurely

        if not parent_node.children:
            parent_node.children[:] = [MinimaxNode(action) for action in self.board.possible_actions(player)]

        assert self.board.has_moves(player)

        # A sorted list will significantly speed up alpha-beta pruning
        if any(child.score is not None for child in parent_node.children):
            parent_node.children.sort(
                key=lambda child: child.score if child.score is not None else +INF,
                reverse=True
            )

        for child in parent_node.children:
            self.board.act(child.action)
            score = self.minimax(depth - 1, child, timer, alpha, beta, not maximizing)[0].score
            child.score = score
            self.board.undo()

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

            if timer.timeouts_soon():
                exited_prematurely = True
                break
            # il est plus rapide de retourner la 1e meilleure action que gérer une liste et choisir un nombre aléatoire
        parent_node.score = alpha if player == self.player_id else beta
        return best_child, exited_prematurely

    def monte_carlo(self, starting_player, num_simulations):
        res = 0
        for sim in range(num_simulations):
            testing_board = deepcopy(self.board)
            winner = None  # on suppose que la partie n'est pas encore gagnante
            this_player_turn = starting_player == self.player_id
            while winner is None:
                curr_player = self.player_id if this_player_turn else self.other_player_id
                # bien que peu efficace, un mouvement + aléatoire, nécessite la génération de toutes les actions
                act = self.random_board_action(testing_board, curr_player)
                testing_board.act(act)

                this_player_turn = not this_player_turn
                winner = testing_board.status.winner
            res += 1 if winner == self.player_id else -1

        return res / num_simulations

    def objective_function(self, curr_player):
        res = 0

        # mobility
        this_player_moves = sum(len(self.possible_moves(queen)) for queen in self.board.queens[self.player_id])
        other_player_moves = sum(len(self.possible_moves(queen)) for queen in self.board.queens[self.other_player_id])

        # territory
        branching = (this_player_moves + other_player_moves) >> 1
        # if near endgame, evaluate reachability
        if branching < 20:
            territory_score, reachability_score = self.territorial_evaluation()
            res += self.m_t * territory_score + self.m_r * reachability_score

        # Monte Carlo winning probability simulation
        winning_prob = self.monte_carlo(curr_player, 10)
        print(winning_prob)

        res += (this_player_moves - other_player_moves) * self.m_m + 100 * winning_prob

        return res

    def branching_factor(self):
        return len(
            list(self.board.possible_actions(self.player_id)) +
            list(self.board.possible_actions(self.other_player_id))
        )

    def mobility_evaluation(self):
        this_player_moves = sum(len(self.possible_moves(queen)) for queen in self.board.queens[self.player_id])
        other_player_moves = sum(len(self.possible_moves(queen)) for queen in self.board.queens[self.other_player_id])
        return this_player_moves - other_player_moves

    def territorial_evaluation(self):
        grids = {}
        for player in (self.player_id, self.other_player_id):
            grids[player] = matrix.Matrix(self.board.N, 0)
            for queen in self.board.queens[player]:
                self.label_territory(grids[player], queen, player)

        territory_score = 0
        reachability_score = 0
        for r in range(self.board.N):
            for c in range(self.board.N):
                pos = matrix.Pos2D(r, c)

                this_player = grids[self.player_id][pos]
                other_player = grids[self.other_player_id][pos]

                # le joueur qui accède le plus vite à la case l'a dans son territoire
                if this_player > 0:
                    reachability_score += 1
                if this_player < other_player:
                    territory_score += 1
                if other_player < this_player:
                    territory_score -= 1

        return territory_score, reachability_score

    def random_board_action(self, board, player):
        """
        La distribution des actions possibles de cette fonction ne sont pas véritablement aléatoires...
        mais ça prendrait bcp trop de temps sinon
        """
        queens = deepcopy(board.queens[player])
        random.shuffle(queens)
        for queen in queens:
            moves = []

            action = [queen]
            directions = list(deepcopy(DIRECTIONS))

            for dir in directions:
                pos = action[0].copy() + dir
                while board.is_valid_pos(pos) and board.grid[pos] is EMPTY:
                    moves.append(pos.copy())
                    pos += dir
                if not moves:
                    continue

            for i in range(2):
                moves = []

                directions = list(deepcopy(DIRECTIONS))
                random.shuffle(directions)

                for dir in directions:
                    pos = action[i].copy() + dir
                    while board.is_valid_pos(pos) and board.grid[pos] is EMPTY:
                        moves.append(pos.copy())
                        pos += dir
                    if not moves:
                        continue
                try:
                    action.append(random.choice(moves))
                except Exception as e:
                    print(queen, "\n", board)
                    raise e
                if len(action) == 3:
                    return Action(*action, player)


    def possible_moves(self, from_pos):
        res = []
        for direction in DIRECTIONS:
            curr_pos = from_pos.copy()
            while True:
                curr_pos += direction
                if not self.board.is_valid_pos(curr_pos) or self.board.grid[curr_pos] != EMPTY:
                    break
                res.append(curr_pos.copy())
        return res

    def label_territory(self, grid, from_pos, player, move_id=1):
        for pos in self.possible_moves(from_pos):

            # labelliser les cases avec la distance négative pour l'adversaire (pour faciliter les calculs)
            grid_val = grid[pos]
            if grid_val == 0 or move_id < grid_val:
                grid[pos] = move_id
                self.label_territory(grid, pos.copy(), player, move_id + 1)



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

    def timeouts_soon(self, threshold=0.15):
        try:
            return self.__time_limit <= self.time + threshold
        except TypeError:
            raise ValueError("No time limit defined")
