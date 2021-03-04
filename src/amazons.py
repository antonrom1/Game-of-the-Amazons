"""
Nom:            ROMANOVA
Prénom:         Anton
Matricule:      521935
Section:        BA1-INFO

src.py
"""

from src.constantes import *
from src.board import Board
from src.player import Player
from src.cell import Piece
from src.geometry import Coord
from random import choice
import os


class Amazons:
    """
    Amazons() -> Amazons
    Amazons(board)
    Implémentation du jeu des Amazones avec une interface en ligne de commandes. Le jeu se démarre par un appel de la
    méthode play. Ensuite le joueur est demandé d'entrer des coups. Il peut joueur contre un autre joueur, ou alors
    contre une IA implémentée à l'aide de l'algorithme minimax (auquel cas, l'utilisateur jouera pour les blancs).
    La partie se termine soit lorsqu'un joueur ne peut plus bouger (celui-ci sera le joueur perdant), soit, dans le cas
    où tous les joueurs dans des zones séparées, si le programme arrive à compter le nombre de coups restants.
    """
    def __init__(self, board=None, use_ai=True, white_opens=True):
        """
        Initialise la classe Amazons
        params:
            board (optionnel): NoneType or str or Board:
                si None est utilisé, le plateau sera initialisé à un plateau par défaut,
                si str est utilisé (en tant que chemin vers le fichier de plateau), le plateau sera initialisé à partir
                    de ce chemin
                si Board est utilisé, le plateau sera la copie de celui-ci

            use_ai (optionnel): Bool
                Utiliser ou non l'IA pour le joueur noir
        """
        if isinstance(board, Board):
            self.__board = board.copy()
        else:
            self.__board = Board.load_board(board) if board is not None else Board.default_board()
        self.__use_ai = use_ai
        self.__curr_player = Player.WHITE if white_opens else Player.BLACK

        self.__winner = None
        self.__scores = {Player.WHITE: 0, Player.BLACK: 0}
        self.__update_game_status()

    @property
    def curr_player(self):
        """
        Le joueur actif
        return: Player
        """
        return self.__curr_player

    @property
    def using_ai(self):
        """
        Si l'IA est utilisée pour le joueur noir ou non
        return: Bool
        """
        return self.__use_ai

    @property
    def scores(self):
        """
        Renvoie la copie du dictionnaire avec le score des joueurs. Le score est à 0 si le jouer n'a ni gagné,
        ni perdu, 1 si il a gagné, sinon -1.
        return:
            {Player: Int}
        """
        return self.__scores.copy()

    @property
    def winner(self):
        """Renvoie le gagnant de la partie si il y en a un, None sinon."""
        return self.__winner

    @property
    def game_ended(self):
        """Renvoie si oui ou non le jeu est terminé"""
        return self.winner is not None

    def __change_player(self):
        # Change de joueur
        self.__curr_player = self.curr_player.other_side()

    def play(self):
        """Joueur au jeu des Amazones tant que le jeu ne sera pas terminé."""
        while not self.game_ended:

            if not (self.using_ai and self.curr_player == Player.BLACK):
                print(self.__board)
                self.__user_move()
                self.__update_game_status()
                self.__change_player()

            if self.using_ai:
                assert self.curr_player == Player.BLACK, "Houston we've got a problem..."
                print("L'IA réfléchit...")
                ai_move = self.__ai_move()
                if ai_move is not None:
                    self.__update_game_status()
                    self.__change_player()
                    ai_move_str = INPUT_SEPARATOR.join(str(p) for p in ai_move)
                    print("L'IA a joué:", ai_move_str)

            # clear up the terminal for the user
            os.system('cls' if os.name == 'nt' else 'clear')
        self.show_endgame_mess()

    def show_endgame_mess(self):
        print(self.__board)
        print(f"Le joueur {self.winner} a gagné!")

    def __user_move(self):
        # appelle le joueur à entrer un coup en input (en boucle tant que celui-ci n'est pas valide),
        # puis applique ce coup.
        succ = False
        while not succ:
            move = input(INPUT_MESS.format(self.curr_player))
            try:
                source, dest, arr = (Coord(pos) for pos in move.split(INPUT_SEPARATOR))
            except (IndexError, ValueError):
                print(INPUT_ERR)
            else:
                try:
                    self.__board.move(source, dest, arr, self.curr_player)
                    succ = True
                except ValueError as e:
                    print(e)

    def who_wins(self):
        """
        Renvoie quel joueur gagne ou non.
        return:
            {Player: bool}
        """
        res = {player: False for player in Player}
        # d'abord tester si la partie n'est pas déjà terminée
        for player in res.keys():
            for pos in self.__board.get_positions(player.piece):
                if self.__board.possible_moves(pos, get_one_value=True):
                    res[player] = True  # le joueur player peut encore bouger
                    break

        if all(res.values()):
            # tous les joueurs peuvent encore bouger
            moves = self.__board.count_remaining_moves()
            if moves is not None:
                white_moves = moves[Player.WHITE]
                black_moves = moves[Player.BLACK]

                res[Player.WHITE] = white_moves > black_moves
                res[Player.BLACK] = black_moves > white_moves

        return res

    def __update_game_status(self):
        # met à jour les propriétés __winner et __scores avec les données actuelles
        winner, white_score, black_score = self.__game_status()
        self.__winner = winner
        self.__scores = {Piece.WHITE: white_score, Piece.BLACK: black_score}

    def __game_status(self):
        # renvoie le gagnant (ou None pas de gagnant) et les scores des joueurs blancs et noirs respectivement
        # les scores sont des int est sont mis à 0 si le joueur ne gagne pas et 1 si le joueur gagne
        who_wins = self.who_wins()
        if not any(who_wins.values()):
            winner = self.__curr_player
        elif all(who_wins.values()):
            winner = None
        else:
            winner = next(player for player, _can_move in who_wins.items() if _can_move)
        return winner, int(winner == Player.WHITE), int(winner == Player.BLACK)

    def __ai_move(self):
        move = self.__minimax()[0]
        if move is not None:  # ai found a move
            try:
                self.__board.move(*move, curr_player=Player.BLACK)
            except ValueError as e:
                print(e)
                raise AssertionError("Une erreur imprévue s'est produite dans le comportement de l'IA")
        else:  # if there are no possible moves for minimax
            self.__winner = self.curr_player
        return move

    def __minimax(self, depth=2, maxi=True, player=Player.BLACK):
        """
        Une simple implémentation de d'un algorithme minimax: simule tous les scénarios de jeu possibles pour
        profondeur coups suivants et renvoie le meilleur.

        La fonction joue du point de vue du joueur noir.
        Renvoie un tuple avec le meilleur coup (ou None si aucun coup est possible) ainsi que son score.
        Le score est calculé de manière suivante: score = score_noir - score_blanc.
        Il est toujours calculé du point de vue du joueur noir.

        return: (Coord, Coord, Coord), NoneType ou int: le meilleur coup (None si aucun coup est possible) et le score
        de la partie
        """
        winner, white_score, black_score = self.__game_status()
        if not depth or winner is not None:
            return None, black_score - white_score

        best_score = -1000 if maxi else 1000
        best_move = []
        player_pos = self.__board.get_positions((player if maxi else player.other_side()).piece)

        for i, source in enumerate(player_pos):
            possible_queen_moves = self.__board.possible_moves(source)
            for j, queen_move in enumerate(possible_queen_moves):
                self.__board.swap_pieces(source, queen_move)
                for arrow_move in self.__board.possible_moves(queen_move):
                    self.__board[arrow_move].piece = Piece.ARROW
                    score = self.__minimax(depth - 1, not maxi, player)[1]
                    move = (source, queen_move, arrow_move), score
                    if (best_score < score) and maxi or (best_score > score) and (not maxi):
                        best_score = score
                        best_move = [move]
                    elif best_score == score:
                        best_move.append(move)
                    self.__board[arrow_move].piece = Piece.EMPTY
                self.__board.swap_pieces(source, queen_move)
        return choice(best_move)  # renvoie au hasard si len(meilleur_coup) > 1
