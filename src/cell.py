from enum import Enum, auto
from src.constantes import WHITE_CHAR, BLACK_CHAR, ARROW_CHAR, EMPTY_CHAR
import src.player as player


class Cell:
    """Une cellule d'un plateau qui a deux propriétés: piece (Piece) et label (int)"""

    def __init__(self, piece, label=0):
        self.piece = piece
        self.label = label

    def __repr__(self):
        return f'Cell(piece={repr(self.piece)}, label={repr(self.label)})'


class Piece(Enum):
    """
    Enumeration des pieces disponibles dans le jeu Amazones

    Méthodes:

    __str__():
        renvoie le caractère représentant le contenu de la cellule
    """
    EMPTY = auto()
    WHITE = auto()
    BLACK = auto()
    ARROW = auto()

    @property
    def player(self):
        """
        Renvoie le joueur (Player) qui joue avec la piece donnée (self). Si la pièce n'appartient pas à un
        joueur, (ex: ARROW, NONE), None est renvoyé
        """
        if self == self.WHITE:
            return player.Player.WHITE
        if self == self.BLACK:
            return player.Player.BLACK

    def __str__(self):
        """Renvoie le caractère (str) représentant visuellement le contenu de la cellule"""
        if self == self.WHITE:
            char = WHITE_CHAR
        elif self is self.BLACK:
            char = BLACK_CHAR
        elif self is self.ARROW:
            char = ARROW_CHAR
        else:
            char = EMPTY_CHAR
        return char

    def __repr__(self):
        """Renvoie une représentation de la pièce sous forme de str"""
        if self == self.WHITE:
            name = 'WHITE'
        elif self is self.BLACK:
            name = 'BLACK'
        elif self is self.ARROW:
            name = 'ARROW'
        else:
            name = 'EMPTY'

        return name
