"""
Nom:            ROMANOVA
Prénom:         Anton
Matricule:      521935
Section:        BA1-INFO

cell.py
"""

from enum import Enum
import src.cell as cell


class Player(Enum):
    """
    Les joueurs possibles dans le jeu Amazones
    """
    WHITE = 1
    BLACK = 2

    def other_side(self):
        """Renvoie l'adversaire du joueur"""
        return Player.BLACK if self == Player.WHITE else Player.WHITE

    @property
    def piece(self):
        """Renvoie la pièce utilisée par le joueur"""
        return cell.Piece.WHITE if self == Player.WHITE else cell.Piece.BLACK

    def __str__(self):
        if self == self.WHITE:
            return "blanc"
        elif self == self.BLACK:
            return "noir"

    def __repr__(self):
        return f'Player.{self.name}'
