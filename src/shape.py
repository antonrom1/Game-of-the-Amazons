import src.geometry as geo
from enum import Enum, auto
from itertools import combinations
from math import isclose


class Shape(Enum):
    """
    Enumeration et détection des formes non-défectives connues.
    Il est possible de directement obtenir la forme à partir d'un nuage de points avec la méthode
    get_shape(cls, point_cloud).
    """

    TRIG = auto()
    LINE = auto()
    RECT = auto()
    POINT = auto()
    UNKNOWN = auto()

    @classmethod
    def get_shape(cls, point_cloud):
        """
        Renvoie la forme Shape à partir du nuage de points point_cloud [Coord].
        Si la forme n'est pas connue, Shape.UNKNOWN est renvoyé
        """
        res = cls.UNKNOWN

        if not isinstance(point_cloud, set):
            TypeError('Point cloud doit être de type set')
        hull_verts = geo.Hull(point_cloud).vertices

        if len(point_cloud) == 1:
            res = cls.POINT
        elif cls.__is_line(hull_verts):
            res = cls.LINE
        elif cls.__is_trig(hull_verts, point_cloud):
            res = cls.TRIG
        elif cls.__is_rect(hull_verts, point_cloud):
            res = cls.RECT
        return res


    @staticmethod
    def __is_trig(hull_verts, point_cloud):
        # méthode booléenne qui renvoie si le nuage de points est un triangle de type 1 ou 2 (comme spécifié
        # dans l'énoncé)
        res = False
        if len(hull_verts) == 3:
            edges = combinations(hull_verts, 2)
            distances_sq = sorted([(edge, edge[0].distance_sq(edge[1])) for edge in edges], key=lambda e: e[1])
            hypot_verts, hypot_length = distances_sq.pop()
            # vérifier si le triangle est rectangle
            if isclose(hypot_length, sum(map(lambda x: x[1], distances_sq))):
                a = (set(hull_verts) - set(hypot_verts)).pop()  # l'angle en ce point est l'angle droit
                b, c = hypot_verts

                res = Shape.__is_trig_type1(point_cloud, a, b, c) or Shape.__is_trig_type2(point_cloud, a, b, c)
        return res

    @staticmethod
    def __is_trig_type2(point_cloud, a, b, c):
        # méthode booléenne qui renvoie si le nuage de points point_cloud est un triangle de type 2
        res = False
        min_y = min(a.y, b.y, c.y)
        max_y = max(a.y, b.y, c.y)
        max_x = max(a.x, b.x, c.x)
        min_x = min(a.x, b.x, c.x)
        if b.x == c.x or b.y == c.y:
            horizontal = a.y == max_y or a.y == min_y
            trig_height = max_y - min_y if horizontal else max_x - min_x
            if not trig_height == (max_x - min_x if horizontal else max_y - min_y) / 2:
                return False
            for i in range(trig_height + 1):
                h_w = i if (a.y == max_y if horizontal else a.x == max_x) else trig_height - i
                for j in range(-trig_height + h_w, trig_height - h_w + 1):
                    y = min_y + i if horizontal else a.y + j
                    x = a.x + j if horizontal else min_x + i
                    if not geo.Coord((x, y)) in point_cloud:
                        return False
            res = True
        return res

    @staticmethod
    def __is_trig_type1(point_cloud, a, b, c):
        # méthode booléenne qui renvoie si le nuage de points point_cloud est un triangle de type 1
        res = False
        min_y = min(a.y, b.y, c.y)
        if (a.x == b.x or a.x == c.x) and (a.y == b.y or a.y == c.y):
            height = max(a.y, b.y, c.y) - min_y
            increment_x = max(a.x, b.x, c.x) > a.x
            bottom_base = min_y == a.y
            for dy in range(height):
                max_dx = height - dy if bottom_base else height
                for dx in range(max_dx):
                    x = a.x + dx * (1 if increment_x else -1)
                    y = min_y + dy
                    if not geo.Coord((x, y)) in point_cloud:
                        return False
            res = True
        return res

    @staticmethod
    def __is_line(hull_verts):
        # méthode booléenne qui renvoie si le nuage de points représenté par son enveloppe convexe (hull_verts)
        # est une droite ou non
        res = False
        if len(hull_verts) == 2:
            (x1, y1), (x2, y2) = hull_verts
            res |= x1 == x2  # ligne verticale
            if not res:
                res |= y1 == y2  # ligne horizontale
            if not res:
                res |= abs((x2 - x1) / (y2 - y1)) == 1  # ligne diagonale
        return res

    @staticmethod
    def __is_rect(hull_verts, point_cloud):
        # méthode booléenne qui renvoie si le nuage de points donné est un rectangle ou non
        res = False
        if len(hull_verts) == 4:
            verts = sorted(hull_verts, key=lambda p: (p.x, p.y))
            if verts[0].x == verts[1].x and verts[2].x == verts[3].x and \
                    verts[0].y == verts[2].y and verts[1].y == verts[3].y:
                # l'enveloppe est rectangulaire
                # generation de tous les points nécessaires pour que ce soit un rectangle
                point_cloud = point_cloud.copy()
                for x in range(verts[0].x, verts[2].x + 1):
                    for y in range(verts[0].y, verts[1].y + 1):
                        if not geo.Coord((x, y)) in point_cloud:
                            return False
                res = True
        return res
