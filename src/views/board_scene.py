from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QGraphicsSceneMouseEvent
from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPen, QColorConstants

from src.const import QUEEN_ICONS, PLAYERS


class BoardScene(QGraphicsScene):

    MOVE_TO_COLOR = QColor(200, 244, 100)
    POSSIBLE_MOVE_INDICATOR_COLOR = QColorConstants.White
    POSSIBLE_MOVE_INDICATOR_COLOR_HIGHLIGHTED = QColorConstants.Red

    def __init__(self, board_delegate, scene_delegate, n, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installEventFilter(self)

        self.board_delegate = board_delegate
        self.scene_delegate = scene_delegate

        self.queens_pixmaps = {player: QPixmap(QUEEN_ICONS[player]) for player in PLAYERS}

        self.n = n
        self.size = 0
        self.top_right = QPointF(0, 0)
        self.tile_size = self.size / self.n
        self._pieces = {}
        self._pieces_items = {}

        self.move_to_tile_pos = None

        self.tile_brushes = QBrush(QColor(175, 50, 50, 255)), QBrush(QColor(255, 215, 200, 255))

        self.selectionChanged.connect(self.selection_changed)

        self._tiles = {}

        self.outlined_tiles_coords = []
        self.outlined_tiles = {}
        self.prev_tile_under_mouse_pos = None
        self.selected_piece = None
        self.selected_piece_original_coordinates = None
        self.show_tile_under_mouse = False

        self._draw()

    def _draw(self):
        pen = QPen(Qt.transparent)

        for i in range(self.n):
            for j in range(self.n):
                brush = self.piece_brush(i, j)
                tile_rect = self.get_tile_rect(i, j)
                self._tiles[(i, j)] = self.addRect(tile_rect, pen, brush)

        self.draw_pieces()

    def get_tile_rect(self, i, j):
        return QRectF(
            self.top_right.x() + j * self.tile_size,
            self.top_right.y() + i * self.tile_size,
            self.tile_size,
            self.tile_size
        )

    def resize(self, rect):
        self.size = min(rect.height(), rect.width())
        self.top_right = rect.center() - QPointF(*(self.size / 2,) * 2)

        self.tile_size = self.size / self.n
        for tile_pos, tile in self._tiles.items():
            tile.setRect(self.get_tile_rect(*tile_pos))

        pixmaps = self.get_scaled_pieces_pixmaps()
        for piece_pos, piece in self._pieces_items.items():
            piece_rect = self.get_tile_rect(*piece_pos)
            piece.setPos(piece_rect.x(), piece_rect.y())
            piece.setPixmap(pixmaps[self._pieces[piece_pos]])

    def get_scaled_pieces_pixmaps(self):
        return {player: self.get_scaled_player_pixmap(player) for player in PLAYERS}

    def piece_brush(self, i, j):
        return self.tile_brushes[(i + j) % 2]

    def redraw_pieces(self):
        for pos, piece_item in self._pieces_items.items():
            self.removeItem(piece_item)
        self.draw_pieces()

    def draw_pieces(self):
        """
        Ajoute toutes les pièces de self._all_pieces à la scène
        sans supprimer les pièces qui sont déjà dans la scène.
        """
        scaled_pixmaps = self.get_scaled_pieces_pixmaps()
        for pos, player in self._pieces.items():
            self._draw_piece_from_prescaled_pixmap(pos, scaled_pixmaps[player])

    def get_scaled_player_pixmap(self, player):
        """
        Renvoie l'image de la reine du joueur ``player`` comme QPixmap à l'échelle d'une case tu plateau
        """
        original_pixmap = self.queens_pixmaps[player]
        return original_pixmap.scaled(*(int(self.tile_size),) * 2,
                                      transformMode=Qt.SmoothTransformation)

    def _draw_piece_from_prescaled_pixmap(self, pos, pixmap):
        """
        Ajoute pixmap à la scène à la piece_position pos.
        pos: (int, int): piece_position sous forme (i, j)
        pixmap: QPixmap qui est déjà à l'échelle d'une case du plateau
        """
        pixmap_item = self.addPixmap(pixmap)
        rect = pixmap_item.mapRectFromParent(self._tiles[pos].rect())
        pixmap_item.setPos(rect.topLeft())
        pixmap_item.setFlag(QGraphicsItem.ItemIsSelectable)

        self._pieces_items[pos] = pixmap_item

    # def add_piece(self, pos, player):
    #     """
    #     ajoute la pièce du joueur player à la piece_position pos de la scène
    #     pos: (int, int): piece_position sous forme (i, j)
    #     player: int: le joueur PLAYER_1 ou PLAYER_2
    #     """
    #     if pos in self._pieces:
    #         raise ValueError('Il y a déjà une pièce dans cette case')
    #     if player not in PLAYERS:
    #         raise ValueError(f"{player} n'est pas un joueur")
    #     self._pieces[pos] = player


    def hide_outlied_tiles(self):
        if self.selected_piece is not None:
            # la reine a été desélectionnée. remettre les tiles à leur couleur normale
            while self.outlined_tiles:
                ellipse = self.outlined_tiles.popitem()[1]
                self.removeItem(ellipse)
            for tile_pos in self.outlined_tiles_coords:
                self._tiles[tile_pos].setBrush(self.piece_brush(*tile_pos))
            self.selected_piece = None

    def add_pieces(self, players):
        self._pieces.update(players)
        self.redraw_pieces()

    def redraw(self, n, rect):
        self.n = n

        self.size = min(rect.height(), rect.width())
        self.top_right = rect.center() - QPointF(*(self.size / 2,) * 2)

        self.tile_size = self.size / self.n
        self.clear()
        self._draw()

    def set_tile_color(self, tile_pos, color):
        tile = self._tiles[tile_pos]
        tile_brush = tile.brush()
        tile_brush.setColor(color)
        tile.setBrush(tile_brush)

    def get_outlined_tile_at_coord(self, piece_pos: QPointF):
        """
        Cherche la case sur laquelle la reine va atterrir si l'utilisateur relâche la souris
        Pour ce faire, il trouve la case avec laquelle l'intersection est la plus grande. Si aucune ne peut être
        trouvée, la case d'origine est renvoyée.
        """
        # puis essayer de trouver une case dont avec une plus grande intersection
        for tile_pos in self.outlined_tiles_coords:
            tile = self._tiles[tile_pos]
            if tile.rect().contains(piece_pos):
                return tile_pos
        return None


    def selection_changed(self):
        selected = self.selectedItems()
        if selected:
            # une reine a été sélectionnée
            self.hide_outlied_tiles()
            self.selected_piece = selected[0]

            self.show_tile_under_mouse = True

            # coordonnée de la reine sélectionnée
            selected_coords = next(coord for coord in self._pieces_items
                                   if self._pieces_items[coord] is self.selected_piece)

            # coordonnées des cases atteignables
            self.outlined_tiles_coords = self.board_delegate.piece_selected(selected_coords)

            # changer de couleur de toutes les cases qui sont atteignables par la reine
            for tile_pos in self.outlined_tiles_coords:
                pen = QPen(QColorConstants.Transparent)
                brush = QBrush(self.POSSIBLE_MOVE_INDICATOR_COLOR)
                tile_rect = self._tiles[tile_pos].sceneBoundingRect()

                center = tile_rect.center()
                tile_rect.setSize(tile_rect.size() / 5)
                tile_rect.moveCenter(center)

                ellipse = self.addEllipse(tile_rect, pen, brush)
                self.outlined_tiles[tile_pos] = ellipse
        else:
            self.show_tile_under_mouse = False
            # remettre les cases atteignables par la reine à leur couleur normale
            self.hide_outlied_tiles()

    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        super(BoardScene, self).mouseMoveEvent(event)
        if self.show_tile_under_mouse:
            tile_pos = self.get_outlined_tile_at_coord(event.scenePos())

            if self.prev_tile_under_mouse_pos == tile_pos:
                return

            if self.prev_tile_under_mouse_pos is not None:
                # set previous highlighted move indicator color back to its original state
                tile = self.outlined_tiles[self.prev_tile_under_mouse_pos]
                tile.setBrush(self.POSSIBLE_MOVE_INDICATOR_COLOR)

            self.prev_tile_under_mouse_pos = tile_pos

            if tile_pos is not None:
                # the mouse is on a valid move tile, so highlight the indicator
                tile = self.outlined_tiles[tile_pos]
                tile.setBrush(QBrush(self.POSSIBLE_MOVE_INDICATOR_COLOR_HIGHLIGHTED))
                self.scene_delegate.change_cursor(Qt.PointingHandCursor)
            else:
                self.scene_delegate.change_cursor(Qt.ArrowCursor)

        elif self.prev_tile_under_mouse_pos is not None:
            tile = self._tiles[self.prev_tile_under_mouse_pos]
            tile.setBrush(self.piece_brush(*self.prev_tile_under_mouse_pos))
            self.scene_delegate.change_cursor(Qt.ArrowCursor)
            self.prev_tile_under_mouse_pos = None



class BoardSceneDelegate:
    def change_cursor(self, cursor):
        raise NotImplemented

class BoardDelegate:
    def piece_selected(self, coord) -> [tuple]:
        raise NotImplemented

    def piece_moved(self, coord):
        raise NotImplemented
