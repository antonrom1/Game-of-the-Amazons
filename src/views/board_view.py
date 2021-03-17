from PyQt5 import QtWidgets
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRectF, QEvent, QObject, QPointF, QSizeF
from PyQt5.QtGui import QBrush, QPen, QColor, QResizeEvent, QPixmap
import sys
from src.const import PLAYER_1, PLAYER_2, RESSOURCES, PLAYERS
import src.players as players
class BoardView(QtWidgets.QGraphicsView):
    MIN_TILE_SIZE = 25

    def __init__(self, n, parent, *args, **kwargs):
        self.board_scene = BoardScene(n, parent)
        super().__init__(self.board_scene, *args, **kwargs)

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.setMinimumSize(*(self.MIN_TILE_SIZE * n,) * 2)
        self.n = n

        self.board_scene.add_pieces({(1, 1): PLAYER_1, (2, 3): PLAYER_2})
        self.board_scene.redraw(n, self.rect())

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        self.board_scene.redraw(self.n, self.rect())


class BoardScene(QtWidgets.QGraphicsScene):

    def __init__(self, n, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installEventFilter(self)

        self.queens_pixmaps = {player: QPixmap(RESSOURCES[player]) for player in PLAYERS}

        self.n = n
        self.size = 0
        self.top_right = QPointF(0, 0)
        self.tile_size = self.size / self.n
        self._pieces = {}
        self._pieces_items = {}

        self._tiles = {}

        self._draw()

    def _draw(self):

        brush1 = QBrush(QColor(175, 50, 50, 255))
        brush2 = QBrush(QColor(255, 215, 200, 255))

        pen = QPen(Qt.transparent)

        for i in range(self.n):
            for j in range(self.n):
                brush = brush1 if (i + j) % 2 else brush2
                tile_rect = QRectF(self.top_right.x() + j * self.tile_size, self.top_right.y() + i * self.tile_size,
                                   self.tile_size, self.tile_size)
                self._tiles[(i, j)] = self.addRect(tile_rect, pen, brush)

        self.draw_pieces()

    def redraw_pieces(self):
        for pos, piece_item in self._pieces_items.items():
            self.removeItem(piece_item)
        self.draw_pieces()

    def draw_pieces(self):
        """
        Ajoute toutes les pièces de self._all_pieces à la scène
        sans supprimer les pièces qui sont déjà dans la scène.
        """
        scaled_pixmaps = {player: self.get_scaled_player_pixmap(player) for player in PLAYERS}
        for pos, player in self._pieces.items():
            self._draw_piece_from_prescaled_pixmap(pos, scaled_pixmaps[player])

    def get_scaled_player_pixmap(self, player):
        """
        Renvoie l'image de la reine du joueur ``player`` comme QPixmap à l'échelle d'une case tu plateau
        """
        original_pixmap = self.queens_pixmaps[player]
        return original_pixmap.scaled(*(int(self.tile_size),) * 2,
                                      transformMode=Qt.SmoothTransformation)

    def draw_piece(self, pos, player):
        """
        Ajoute la pièce de player à la scène à la position pos
        pos: (int, int): position sous forme (i, j)
        player: int: PLAYER_1 ou PLAYER_2
        """
        pixmap = self.get_scaled_player_pixmap(player)
        self.draw_piece_from_prescaled_pixmap(pos, pixmap)

    def _draw_piece_from_prescaled_pixmap(self, pos, pixmap):
        """
        Ajoute pixmap à la scène à la position pos.
        pos: (int, int): position sous forme (i, j)
        pixmap: QPixmap qui est déjà à l'échelle d'une case du plateau
        """
        pixmap_item = self.addPixmap(pixmap)
        rect = pixmap_item.mapRectFromParent(self._tiles[pos].rect())
        pixmap_item.setPos(rect.topLeft())
        pixmap_item.setFlag(QGraphicsItem.ItemIsSelectable)

        self._pieces_items[pos] = pixmap_item

    def add_piece(self, pos, player):
        """
        ajoute la pièce du joueur player à la position pos de la scène
        pos: (int, int): position sous forme (i, j)
        player: int: le joueur PLAYER_1 ou PLAYER_2
        """
        if pos in self._pieces:
            raise ValueError('Il y a déjà une pièce dans cette case')
        if player not in PLAYERS:
            raise ValueError(f"{player} n'est pas un joueur")
        self._pieces[pos] = player

    def add_pieces(self, players):
        self._pieces.update(players)
        self.redraw_pieces()

    def remove_piece(self, pos):
        """
        Supprime la pièce à la position pos de la scène.
        Renvoie True si la pièce existait dans la scène et False sinon
        """
        for player in PLAYERS:
            try:
                self._pieces[player].remove(pos)
            except ValueError:
                continue
            else:
                self.removeItem(self._pieces_items[pos])
                return True
        return False

    def redraw(self, n, rect):
        self.n = n

        self.size = min(rect.height(), rect.width())
        self.top_right = rect.center() - QPointF(*(self.size / 2,) * 2)

        self.tile_size = self.size / self.n
        self.clear()
        self._draw()
