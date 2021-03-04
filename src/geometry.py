import math
from src.constantes import LETTERS_IN_ALPHABET


class Coord:
    """
    Coordinates est une classe représentant les coordonnées d'une cellule.
    """

    __COL_START = "a"
    """
    la lettre du début de l'énumération des colonnes dans le système de coordonnées des échecs (la lettre 
    correspond par exemple à a dans a4)
    """

    __ROW_START = 1
    """
    le numéro du début de l'énumération des colonnes dans le système de coordonnées des échecs (le numéro 
    correspond par exemple à 1 dans e1)
    """

    def __init__(self, coord):
        """
        :param coord: (int, int) ou str: coordonnées de la cellule sous forme de tuple d'entiers ou coordonnées
        d'échiquier (ex: (colonne, ligne) ou "e10")
        """
        self.__x, self.__y = coord if isinstance(coord, tuple) else self.tuple_from_str(coord)

    @staticmethod
    def tuple_from_str(coord):
        """
        Traduit le coup en tuple (ligne, colonne) et change les attributs i et j de la classe.
        coord: str:         une case du plateau sous forme de string, tel que a8 ou e10
        """
        if len(coord) < 2 or not coord[0].isalpha() or not coord[1:].isdigit():
            raise ValueError(f"{coord} n'est pas une coordonnée valide")

        col_str = coord[0]  # la colonne, une seule lettre
        row_str = "".join(coord[1:])  # la ligne, chaîne de characters représentant un nombre

        x = ord(col_str.lower()) - ord(Coord.__COL_START)
        y = int(row_str) - Coord.__ROW_START
        return x, y

    @property
    def x(self):
        """La composante x de la coordonnée"""
        return self.__x

    @property
    def y(self):
        """La composante y de la coordonnée"""
        return self.__y

    def __getitem__(self, n):
        """
        Renvoie la composante à l'indice n de la coordonnée.
        n: int: 0 pour x, 1 pour y
        """
        if isinstance(n, int):
            if n == 0:
                return self.x
            elif n == 1:
                return self.y
        raise IndexError("L'indice de Coord ne peut que être un int valant 0 ou 1")

    def __str__(self):
        """
        Traduit les coordonnées en coup (comme a8 ou e10).
        return: str: la position du coup sous forme de string, tel que a8 ou e10
        """
        try:
            return self.col_str() + self.row_str()
        except ValueError:
            return str((self.x, self.y))

    def __repr__(self):
        return f"Coord({self.x, self.y})"

    def col_str(self):
        """
        Traduit la colonne en colonne de l'échiquier (comme e).
        Si la composante x de la coordonnée ne peut pas être représentée par un caractère de l'alphabet
        ( x < 0 ou > 25), une erreur sera levée
        return: str
        """
        if self.x < 0 or not isinstance(self.x, int):
            raise ValueError("Seulement les coordonnées à composantes entières et positives peuvent être représentées")
        if self.x >= LETTERS_IN_ALPHABET - 1:
            raise ValueError("Impossible de représenter sous forme de lettre une coordonnée d'échiquier dont "
                             "l'abscisse est supérieure à 25")
        return chr(self.x + ord(self.__COL_START))

    def row_str(self):
        """
        Traduit la ligne en ligne de l'échiquier (comme 5).
        return: str
        """
        if self.y < 0 or not isinstance(self.y, int):
            raise ValueError("Seulement les coordonnées à composantes entières et positives peuvent être représentées")
        return str(self.y + 1)

    def distance_sq(self, other):
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2

    def __eq__(self, other):
        """
        Renvoie si les coordonnées des deux cases sont identiques ou non.
        """
        return self[0] == other[0] and self[1] == other[1]

    def __add__(self, other):
        """
        Renvoie la somme des deux coordonnées. Le terme other peut être Coord ou une séquence représentant une
        coordonnée de taille 2
        """
        if not isinstance(other, Coord):
            if len(other) != 2:
                raise ValueError("Une séquence représentant une coordonnée en deux "
                                 "dimensions doit avoir une longueur de 2")
        return Coord((self[0] + other[0], self[1] + other[1]))

    def __iadd__(self, other):
        """
        Renvoie la somme des deux coordonnées. Le terme other peut être Coord ou une séquence représentant une
        coordonnée de taille 2
        """
        return self + other

    def __hash__(self):
        """Renvoie le hash de la coordonnée"""
        return hash((self.x, self.y))


    def in_board(self, board_size):
        """
        :param board_size: la valeur maximale que i et j peuvent avoir
        :return: si les attributs i et j sont compris dans l'intervalle 0 (inclus) et size (exclu)
        """
        is_int = isinstance(self.x, int) and isinstance(self.y, int)
        return is_int and 0 <= self.x < board_size and 0 <= self.y < board_size


class Line:
    """
    Equation générale d'une droite sous forme ax + by + c = 0
    """

    def __init__(self, a, b, c):
        """
        Initialise Line avec les paramètres a, b, c (int ou float).

        L'équation de la droite ne peut pas être une forme indéterminée (a == b == 0). Une erreur sera
        levée si tel est le cas.
        """
        if a == b == 0:
            raise ValueError(f'({a}x + {b}y + {c} = 0) is not an equation of a line.')
        self.__a = a
        self.__b = b
        self.__c = c

    @property
    def a(self):
        """Renvoie la propriété a de l'équation"""
        return self.__a

    @property
    def b(self):
        """Renvoie la propriété b de l'équation"""
        return self.__b

    @property
    def c(self):
        """Renvoie la propriété c de l'équation"""
        return self.__c

    def split_point_cloud(self, s):
        """
        Sépare le nuage de points s (séquence de Coord) en deux sous ensembles, s1 et s2

        Si un point est exactement sur la ligne, il ne sera ni dans s1, ni dans s2
        return:
            set(Coord), set(Coord)
        """
        s0 = set()
        s1 = set()
        for point in s:
            res = self.a * point.x + self.b * point.y + self.c
            if res > 0:
                s0 |= {point}
            elif res < 0:
                s1 |= {point}
        return s0, s1

    def __repr__(self):
        return f"Line({self.a}, {self.b}, {self.c})"

    def __str__(self):
        return f"{self.a}x + {self.b}y + {self.c} = 0"

    @property
    def is_horizontal(self):
        """Renvoie si la représentation graphique de la droite est une droite horizontale ou non"""
        return self.a == 0 and self.b != 0

    @property
    def is_vertical(self):
        """Renvoie si la représentation graphique de la droite est une droite verticale ou non"""
        return self.b == 0 and self.a != 0

    def __eq__(self, other):
        """Renvoie si les deux équations sont équivalentes ou pas"""
        k = other.a / self.a if self.is_horizontal else other.b / self.b
        # isclose pour éviter les erreurs (max d'ordre de 10^-9) possibles causées par la manip de flottants
        if self.is_horizontal:
            cond1 = math.isclose(self.b * k, other.b)
        else:
            cond1 = math.isclose(self.a * k, other.a)
        return cond1 and math.isclose(self.c * k, other.c)

    def distance_sq(self, p: Coord):
        """
        Renvoie la plus petite distance possible au carré entre la droite et le point (Coord) p
        return:
            int ou float
        """
        num = (self.a * p.x + self.b * p.y + self.c) ** 2
        den = self.a ** 2 + self.b ** 2
        res = num / den
        return int(res) if res.is_integer() else res

    def perpendicular(self, point: Coord):
        """Renvoie une instance de Line qui est perpendiculaire à self et qui passe par le point point"""
        a, b = self.b, -self.a
        c = -a * point.x + -b * point.y
        return Line(a, b, c)

    def intersect(self, other):
        """
        Renvoie le point (Coord) d'intersection entre deux instances de Line
        Si les droites sont parallèles, une ValueError sera levée
        """
        d = self.b * other.a - self.a * other.b
        try:
            x = (self.c * other.b - self.b * other.c) / d
        except ZeroDivisionError:
            raise ValueError('Aucune intersection possible entre deux droites parallèles')

        y = (self.a * other.c - self.c * other.a) / d
        x = int(x) if x.is_integer() else x
        y = int(y) if y.is_integer() else y

        return Coord((x, y))

    @classmethod
    def through_two_points(cls, p1: Coord, p2: Coord):
        """
        Renvoie une instance de Line qui traverse les deux points donnés (Coord)

        Si les points sont égaux, une ValueError sera levée
        """
        if p1 == p2:
            raise ValueError('p1 et p2 doivent être des coordonnées différentes')
        x1, y1 = p1
        x2, y2 = p2
        return cls(y2 - y1, x1 - x2, y1 * x2 - x1 * y2)


class Hull:
    """Enveloppe convexe"""
    def __init__(self, s):
        """
        Initialise une instance de Hull

        args:
            s: liste ou set de Coord: un nuage de points à partir duquel l'enveloppe convexe sera générée
        """
        self.__vertices = self.__quickhull(s.copy())

    @property
    def vertices(self):
        """Les coordonnées de l'enveloppe convexe"""
        return self.__vertices

    def __quickhull(self, s):
        # implémentation de l'algorithme de quickhull avec s étant un nuage de points
        if len(s) > 1:
            s = sorted(s, key=lambda c: (c.x, c.y)) # sort est plus rapide que min et max pour des petits ensembles
            a, b = s.pop(0), s.pop()
            hull = {a, b}
            ab_line = Line.through_two_points(a, b)
            s0, s1 = ab_line.split_point_cloud(s)
            for subset in (s0, s1):
                self.__find_hull(subset, a, b, ab_line, hull)
            return hull
        else:
            return s

    def __find_hull(self, s, a, b, ab_line, hull):
        if s:
            c = max(s, key=lambda p: ab_line.distance_sq(p))
            s.remove(c)
            hull |= {c}

            ab_perpendicular = ab_line.perpendicular(c)
            ac_line = Line.through_two_points(a, c)
            bc_line = Line.through_two_points(b, c)

            ac_subsets = ac_line.split_point_cloud(s)
            bc_subsets = bc_line.split_point_cloud(s)
            s1 = s2 = None

            # trouver le coté de la droite qui correspond aux points à l'intérieur et extérieur du triangle
            for i, j in ((i, j) for i in range(2) for j in range(2) if i != j):
                if ac_subsets[i] & bc_subsets[j]:  # si len(intersection), intersection sont les points dans le triangle
                    s1 = ac_subsets[not i]
                    s2 = bc_subsets[not j]
                    break

            new_a, new_b = ab_line.intersect(ab_perpendicular), c
            for subset in (s1, s2):
                self.__find_hull(subset, new_a, new_b, ab_perpendicular, hull)
