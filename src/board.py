"""
Nom:            ROMANOVA
Prénom:         Anton
Matricule:      521935
Section:        BA1-INFO

board.py
"""

from src.constantes import *
from src.cell import Cell, Piece
from src.geometry import Coord
from src.shape import Shape
from src.player import Player
from warnings import warn
from src.ask_user import ask_user_bool


class Board:
    """
    Un plateau carré du jeu des Amazones. La taille est limitée par les cases représentables, càd 26 (colonnes
    représentées par des lettres de l'alphabet).
    """
    def __init__(self, black, white, arrows, size=10):
        """
        Initialise le plateau à partir de coordonnées de pièces du jeu. Les coordonnées sont acceptées soit sous forme
        d'instances de Coord, soit des valeurs acceptées par le constructeur de Coord.

        black:  [Coord ou str (ex: d6) ou (x, y)]: coordonnées des pions noirs
        white:  [Coord ou str (ex: d6) ou (x, y)]: les coordonnées des pions blancs
        arrows: [Coord ou str (ex: d6) ou (x, y)]: les coordonnées des flèches
        size:   int: la taille du plateau
        """
        if not isinstance(size, int):
            raise ValueError("La taille (size) doit être un int")

        if not 1 < size <= 26:
            raise ValueError("La taille du plateau doit être supérieure à 1 et"
                             "ne peut pas dépasser le nombre de lettres disponibles (26)")

        if not black or not white:
            raise ValueError("Le plateau doit contenir au moins une reine de chaque couleur")

        if len(black + white + arrows) != len(set(black + white + arrows)):
            raise ValueError("Les coordonnées des pièces doivent être uniques")

        self.__size = size
        self.__cells = {}

        # place les pièces sur le plateau
        for piece, pieces_pos_str in ((Piece.BLACK, black), (Piece.WHITE, white), (Piece.ARROW, arrows)):
            for pos in pieces_pos_str:
                if not isinstance(pos, Coord):
                    pos = Coord(pos)

                if pos.in_board(size):
                    self.__cells[pos] = Cell(piece)
                else:
                    warn(f"La coordonnée donnée, {str(pos)}, ne rentre pas dans le plateau de taille donné ({size}).\n"
                         "Elle sera donc ignorée.")

        # remplit le reste du plateau avec des cases vides
        for i in range(size):
            for j in range(size):
                self.__cells.setdefault(Coord((i, j)), Cell(Piece.EMPTY))

    @property
    def size(self):
        """Renvoie la taille tu plateau (int)"""
        return self.__size

    def __getitem__(self, item):
        """Renvoie la cellule (Cell) à la coordonnée (Coord) donnée"""
        return self.__cells[item]

    def __setitem__(self, coord, cell):
        """Assigne la cellule (Cell) donnée à la coordonnée (Coord)"""
        if coord.in_board(self.size):
            if not isinstance(cell, Cell):
                raise TypeError("Le type de la valeur assignée doit être Cell")
            self.__cells[coord] = cell
        else:
            raise ValueError(f"{coord} n'est pas dans le plateau")

    def swap_pieces(self, c1, c2):
        """Permute les pieces aux coordonnées c1 et c2"""
        self[c1].piece, self[c2].piece = self[c2].piece, self[c1].piece

    def possible_moves(self, source, get_one_value=False):
        """
        Donne les mouvements possibles depuis la case source, les cases en question sont toutes les cases en ligne
        droite (orthogonale ou diagonale) jusqu'à la rencontre d'un obstacle (reine ou flèche)
        Args:
            source (Coord):
                Position de depart
            get_one_value (Bool):
                renvoie la premiere valeur obtenue (afin de savoir plus rapidement si la piece peut bouger)
        Returns:
            [Coord]:
                Liste des coups possibles
        """
        res = []
        for direction in [(x, y) for x in range(-1, 2) for y in range(-1, 2) if not (x == y == 0)]:
            pos = source
            while True:
                pos += direction
                if not (pos.in_board(self.size) and self[pos].piece == Piece.EMPTY):
                    break
                if get_one_value:
                    return [pos]
                else:
                    res.append(pos)

        return res

    def get_positions(self, piece):
        """Renvoie une liste de coordonnées [Coord] de la piece donnée"""
        return [pos for pos, cell in self.__cells.items() if cell.piece == piece]

    def move(self, source, dest, arrow, curr_player):
        """
        Effectue le coup donné si il est valide. Lève une erreur dans le cas contraire.
        source: Coord:
            coordonnée de la case source
        dest: Coord:
            coordonnée de la case d'arrivée de la reine
        arrow: Coord:
            coordonnée de la case d'arrivée de la flèche
        curr_player: Player:
            le joueur actuel
        """
        if source in self.get_positions(curr_player.piece):
            if dest in self.possible_moves(source):
                self.swap_pieces(source, dest)
                if arrow in self.possible_moves(dest):
                    self[arrow].piece = Piece.ARROW
                else:
                    self.swap_pieces(source, dest)
                    raise ValueError(PATH_ERR)
            else:
                raise ValueError(PATH_ERR)
        else:
            raise ValueError(QUEEN_ERR)

    def __str__(self):
        """Renvoie une représentation formatée du tableau sous forme de chaîne de caractères"""
        res = ""

        # le plateau commence (lecture haut->bas) par le plus grand indice de ligne
        for row in range(self.size):
            line = COL_SEP.join((str(self[col, row].piece) for col in range(self.size)))
            num_ligne = f'{row + 1:<{SPACES_ROW_NUM}}'

            # les nouvelles lignes sont ajoutées avant les anciennes car le plateau
            # commence (lecture haut->bas) par le plus grand indice de ligne
            res = num_ligne + line + ROW_SEP + res

        # la dernière ligne composée de lettres pour les coordonnées (a b c d e f...)
        coord_colonnes = COL_SEP.join([Coord((col, 0)).col_str() for col in range(self.__size)])

        res += " " * SPACES_ROW_NUM + coord_colonnes

        return res

    def __label_all_components(self):
        # labellise toutes les composantes connexes du plateau
        label = 0
        for cell in self.__cells.values():  # reset all labels
            cell.label = label
        for coord in (Coord((x, y)) for x in range(0, self.size) for y in range(0, self.size)):
            cell = self[coord]
            if cell.label == 0 and cell.piece != Piece.ARROW:
                label += 1
                self.__label_component(coord, label)
        return label

    def __label_component(self, coord, label):
        # labellise une composante connexe du plateau
        self[coord].label = label
        for direction in ((x, y) for x in range(-1, 2) for y in range(-1, 2) if not x == y == 0):
            new_coord = coord + direction
            in_board = new_coord.in_board(self.size)
            new_cell = self[new_coord] if in_board else None
            if in_board and new_cell.label == 0 and new_cell.piece != Piece.ARROW:
                self.__label_component(new_coord, label)

    def count_remaining_moves(self):
        """
        Calcule le nombre de mouvements maximum possible pour chaque joueur si ils sont séparés dans des régions
        non-défectives.
        """
        num_labels = self.__label_all_components()
        if num_labels < 2:
            return
        labeled_subsets = {}  # {label_num: [Piece, piece_count, [c1, c2, c3, c4]]}
        for coord, cell in self.__cells.items():
            if 0 < cell.label <= num_labels:
                subset = labeled_subsets.get(cell.label, [Piece.EMPTY, 1, []])
                if subset[0] != cell.piece:
                    if subset[0] != Piece.EMPTY and cell.piece != Piece.EMPTY:
                        return  # au moins une composante connexe contient deux joueurs
                    if subset[0] == Piece.EMPTY:
                        subset[0] = cell.piece
                elif subset[0] != Piece.EMPTY:
                    subset[1] += 1  # il y a plusieurs pieces du même joueur dans la zone
                subset[2].append(coord)
                labeled_subsets[cell.label] = subset

        res = {Player.WHITE: 0, Player.BLACK: 0}
        for piece, piece_count, coords in labeled_subsets.values():
            player = piece.player
            if player is not None and len(coords) > 1:
                # ne pas continuer si il y a un joueur qui est dans une composante à forme inconnue
                if Shape.get_shape(coords) == Shape.UNKNOWN:
                    return
                # queens
                res[player] += len(coords) - piece_count

        return res

    @classmethod
    def load_board(cls, filename):
        """
        Lit les 4 informations sur le plateau dans le fichier donné
        ce fichier doit être structuré comme suit :
        ligne 1 : taille du plateau
        ligne 2 : les positions des reines noires séparées par une virgule sans espace
        ligne 3 : les positions des reines blanches séparées par une virgule sans espace
        ligne 4 : les positions des fleches séparées par une virgule sans espace
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.read().split("\n")
        except IOError:
            raise IOError("Erreur d'ouverture du fichier de jeu.")
        try:
            size = int(lines.pop(0).strip())
            black, white, arrows = [[Coord(coord) for coord in line.split(GAME_FILE_SEPARATOR) if len(coord) > 0]
                                    for line in lines]
        except (ValueError, IndexError) as err:
            print(err)
            print("Le fichier du plateau n'est pas correctement défini")
            # demander à l'utilisateur si il veut lancer une partie avec un plateau par défaut
            if ask_user_bool("Initialiser à un plateau par défaut"):
                return cls.default_board()
            else:
                raise ValueError("Le fichier donné est invalide")
        else:
            return cls(black, white, arrows, size)

    @classmethod
    def default_board(cls):
        """Renvoie le plateau par défaut utilisé dans le jeu des Amazones"""
        return cls(BLACK_DEFAULT_POS, WHITE_DEFAULT_POS, [])

    def copy(self):
        """Renvoie une copie de self"""
        black = self.get_positions(Piece.BLACK)
        white = self.get_positions(Piece.WHITE)
        arrows = self.get_positions(Piece.ARROW)
        size = self.size

        return Board(black, white, arrows, size)
