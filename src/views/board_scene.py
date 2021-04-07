from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsSceneMouseEvent, QGraphicsObject, QGraphicsEllipseItem
from PyQt5.QtCore import QPointF, Qt, QRectF, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QBrush, QPen, QColor
from src.views.sound import AmazonsSound
from src.const import QUEEN_ICONS, PLAYERS, ARROW_ICON, REACHABLE_INDICATOR_SIZE_TO_TILE_SIZE_RATIO
import math


class BoardScene(QGraphicsScene):
    MOVE_TO_COLOR = QColor(200, 244, 100)
    POSSIBLE_MOVE_INDICATOR_COLOR = QColor(255, 255, 255)
    POSSIBLE_MOVE_INDICATOR_COLOR_HIGHLIGHTED = QColor(255, 150, 100)
    ARROW_SIZE_TO_TILE_SIZE_RATIO = 0.4

    def __init__(self, scene_delegate, board_delegate, n, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board_delegate = board_delegate
        self.scene_delegate = scene_delegate

        self.queens_pixmaps = {player: QPixmap(QUEEN_ICONS[player]) for player in PLAYERS}

        self.n = n
        self.pixel_board_size = 0
        self.top_right_point = QPointF(0, 0)
        self.tile_pixel_size = self.pixel_board_size / self.n

        self.pieces = {}
        self.pieces_graphics_items = {}

        self.arrows = []
        self.arrows_graphics_items = {}

        self.tile_brushes = QBrush(QColor(175, 50, 50, 255)), QBrush(QColor(255, 215, 200, 255))

        self.tiles_graphics_items = {}

        self.possible_moves = []
        self.possible_move_indicators_items = {}

        self.prev_tile_under_mouse_pos = None
        self.moving_queen = None
        self.queen_arrow_graphics_item = None
        self.tracking_mouse_for_arrow_rotation = False
        self.highlighting_reachable_tiles_under_mouse = False
        self.can_shoot_arrow = False

        self.can_undo_action = True
        self.listen_mouse_click_events = True

        self.ongoing_action = []

        self.selectionChanged.connect(self.selection_changed)
        self._draw()

    def cleanup_board(self):
        self.tiles_graphics_items = {}

        self.possible_moves = []
        self.possible_move_indicators_items = {}

        self.pieces = {}
        self.pieces_graphics_items = {}

        self.arrows = []
        self.arrows_graphics_items = {}

        self.ongoing_action = []

    def _draw(self):
        pen = QPen(Qt.transparent)

        for i in range(self.n):
            for j in range(self.n):
                brush = self.piece_brush(i, j)
                tile_rect = self.get_tile_rect(i, j)
                self.tiles_graphics_items[(i, j)] = self.addRect(tile_rect, pen, brush)

        self.draw_pieces()

    def get_tile_rect(self, i, j):
        return QRectF(
            self.top_right_point.x() + j * self.tile_pixel_size,
            self.top_right_point.y() + i * self.tile_pixel_size,
            self.tile_pixel_size,
            self.tile_pixel_size
        )

    def allow_pieces_interaction(self, player):
        self.listen_mouse_click_events = True
        for piece_pos, piece_graphical_item in self.pieces_graphics_items.items():
            piece_graphical_item.setFlag(QGraphicsItem.ItemIsSelectable, self.pieces[piece_pos] == player)

    def stop_all_possible_interaction(self):
        self.listen_mouse_click_events = False
        for piece_player, piece_graphical_item in self.pieces_graphics_items.items():
            piece_graphical_item.setFlag(QGraphicsItem.ItemIsSelectable, False)

    def resize(self, rect):
        self.pixel_board_size = min(rect.height(), rect.width())
        self.top_right_point = rect.center() - QPointF(*(self.pixel_board_size / 2,) * 2)

        self.tile_pixel_size = self.pixel_board_size / self.n
        for tile_pos, tile in self.tiles_graphics_items.items():
            tile.setRect(self.get_tile_rect(*tile_pos))

        pixmaps = self.get_scaled_pieces_pixmaps()
        for piece_pos, piece in self.pieces_graphics_items.items():
            piece_rect = self.get_tile_rect(*piece_pos)
            piece.setPos(piece_rect.x(), piece_rect.y())
            piece.setPixmap(pixmaps[self.pieces[piece_pos]])
        for pos, indic in self.possible_move_indicators_items.items():
            indic.setRect(self.get_reachable_tile_indicator_size(pos))

        for arr_pos, arr in self.arrows_graphics_items.items():
            arr.setRect(self.get_arrow_rect(*arr_pos))

    def get_scaled_pieces_pixmaps(self):
        return {player: self.get_scaled_player_pixmap(player) for player in PLAYERS}

    def get_scaled_player_pixmap(self, player):
        """
        Renvoie l'image de la reine du joueur ``player`` comme QPixmap à l'échelle d'une case tu plateau
        """
        original_pixmap = self.queens_pixmaps[player]
        return self.scale_pixmap_tile_size(original_pixmap)

    def get_arrow_rect(self, i, j):
        rect = self.get_tile_rect(i, j)
        self.rescale_at_center(rect, self.ARROW_SIZE_TO_TILE_SIZE_RATIO)
        return rect

    def piece_brush(self, i, j):
        return self.tile_brushes[(i + j) % 2]

    def redraw_pieces(self):
        for pos, piece_item in list(self.pieces_graphics_items.items()) + list(self.arrows_graphics_items.items()):
            self.removeItem(piece_item)
        self.draw_pieces()

    def draw_pieces(self):
        """
        Ajoute toutes les pièces de self._all_pieces à la scène
        sans supprimer les pièces qui sont déjà dans la scène.
        """
        scaled_pixmaps = self.get_scaled_pieces_pixmaps()
        for pos, player in self.pieces.items():
            self._draw_piece_from_prescaled_pixmap(pos, scaled_pixmaps[player])
        for pos in self.arrows:
            self.add_arrow_graphics_item(pos)

    def add_arrow_graphics_item(self, pos):
        pen = QPen(QColor(0, 0, 0, 255))
        brush = QBrush(QColor(0, 0, 0, 255))

        arrow = self.addEllipse(self.get_arrow_rect(*pos), pen=pen, brush=brush)

        self.arrows_graphics_items[pos] = arrow

    def scale_pixmap_tile_size(self, pixmap):
        return pixmap.scaled(*(int(self.tile_pixel_size),) * 2,
                             transformMode=Qt.SmoothTransformation)

    def _draw_piece_from_prescaled_pixmap(self, pos, pixmap):
        """
        Ajoute pixmap à la scène à la piece_position pos.
        pos: (int, int): piece_position sous forme (i, j)
        pixmap: QPixmap qui est déjà à l'échelle d'une case du plateau
        """
        pixmap_item = self.addPixmap(pixmap)
        rect = pixmap_item.mapRectFromParent(self.tiles_graphics_items[pos].rect())
        pixmap_item.setPos(rect.topLeft())

        self.pieces_graphics_items[pos] = pixmap_item

    def hide_marked_tiles(self):
        if self.ongoing_action:
            # remettre les tiles à leur couleur normale
            self.prev_tile_under_mouse_pos = None

            while self.possible_move_indicators_items:
                indicator = self.possible_move_indicators_items.popitem()[1]
                self.removeItem(indicator)
            for tile_pos in self.possible_moves:
                self.tiles_graphics_items[tile_pos].setBrush(self.piece_brush(*tile_pos))

    def add_pieces(self, players):
        self.pieces.update(players)
        self.redraw_pieces()

    def add_arrows(self, arrows):
        self.arrows += arrows

        # flags are saved to make sure that queens that were selectable will still be selectable after the redraw
        temp_flags = {pos: item.flags() for pos, item in self.pieces_graphics_items.items()}

        self.redraw_pieces()

        for pos, item in self.pieces_graphics_items.items():
            flags = temp_flags.get(pos, None)
            if flags is not None:
                item.setFlags(flags)

    def redraw(self, n, rect):
        self.n = n

        self.pixel_board_size = min(rect.height(), rect.width())
        self.top_right_point = rect.center() - QPointF(*(self.pixel_board_size / 2,) * 2)

        self.tile_pixel_size = self.pixel_board_size / self.n
        self.clear()
        self._draw()

    def set_tile_color(self, tile_pos, color):
        tile = self.tiles_graphics_items[tile_pos]
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
        for tile_pos in self.possible_moves:
            tile = self.tiles_graphics_items[tile_pos]
            if tile.rect().contains(piece_pos):
                return tile_pos
        return None

    def deselect_piece(self):
        self.hide_marked_tiles()
        self.highlighting_reachable_tiles_under_mouse = False
        # cacher les marques qui montrent que la case est atteignable

        if self.prev_tile_under_mouse_pos is not None:
            # s les marqueurs  par le glissement de la souris au dessus des cases atteignables
            # tile = self.tiles_graphics_items[self.prev_tile_under_mouse_pos]
            # tile.setBrush(self.piece_brush(*self.prev_tile_under_mouse_pos))
            self.scene_delegate.change_cursor(Qt.ArrowCursor)
            self.prev_tile_under_mouse_pos = None

        self.clearSelection()

    def undo_action(self):
        if self.ongoing_action:
            self.can_shoot_arrow = False
            if len(self.ongoing_action) == 2:
                self.removeItem(self.queen_arrow_graphics_item)
                self.move_piece(self.ongoing_action[0], undoing=True)
            self.deselect_piece()
            self.ongoing_action = []

            # pour cacher le curseur de séléction de case de destination
            self.highlight_reachable_tile_under_mouse(None)

    def select_piece(self, piece):
        """ une reine a été sélectionnée """

        # coordonnée de la reine sélectionnée
        queen_coords = next(coord for coord in self.pieces_graphics_items
                               if self.pieces_graphics_items[coord] is piece)
        try:
            # coordonnées des cases atteignables
            self.possible_moves = self.board_delegate.piece_selected(queen_coords)
        except AttributeError:
            return

        # supprime les marqueurs précédents
        self.hide_marked_tiles()
        self.highlighting_reachable_tiles_under_mouse = True

        self.ongoing_action = [queen_coords]

        self.highlight_reachable_tiles()

    def highlight_reachable_tiles(self):
        # changer de couleur de toutes les cases qui sont atteignables par la reine
        for tile_pos in self.possible_moves:
            brush = QBrush(self.POSSIBLE_MOVE_INDICATOR_COLOR)
            ellipse = self.addEllipse(self.get_reachable_tile_indicator_size(tile_pos), brush=brush)
            self.possible_move_indicators_items[tile_pos] = ellipse

    def get_reachable_tile_indicator_size(self, pos):
        tile_rect = self.tiles_graphics_items[pos].sceneBoundingRect()
        center = tile_rect.center()
        tile_rect.setSize(tile_rect.size() * REACHABLE_INDICATOR_SIZE_TO_TILE_SIZE_RATIO)
        tile_rect.moveCenter(center)
        return tile_rect

    def selection_changed(self):
        selected = self.selectedItems()
        if selected:
            self.select_piece(selected[0])
        else:
            if self.can_undo_action:
                self.undo_action()

    def shoot_arrow(self, to_pos, check_if_move_is_valid=True):
        arrow = self.queen_arrow_graphics_item

        if not isinstance(arrow, QGraphicsItem):
            return

        self.tracking_mouse_for_arrow_rotation = False
        self.highlighting_reachable_tiles_under_mouse = False

        self.highlight_reachable_tile_under_mouse(None)

        self.hide_marked_tiles()
        if len(self.ongoing_action) == 2:
            self.ongoing_action.append(to_pos)

        if check_if_move_is_valid:
            try:
                if not self.board_delegate.is_action_valid(*self.ongoing_action):
                    # l'action est invalide...
                    # ceci ne devrait normalement pas se passer, mais bon... il faut annuler l'action
                    self.ongoing_action.pop()
                    self.removeItem(arrow)
                    self.undo_action()
                    return
            except AttributeError:
                # le joueur n'est pas Humain
                pass

        to_point = self.get_tile_rect(*to_pos).topLeft()

        assert isinstance(arrow, QGraphicsItem)
        self.can_shoot_arrow = False
        AmazonsSound.shared.play_arrow_sfx()
        PieceMoveAnimation(arrow, to_point, easing_curve=QEasingCurve.InBack, finished=self.hide_shot_arrow)

    def hide_shot_arrow(self):
        self.removeItem(self.queen_arrow_graphics_item)
        if len(self.ongoing_action) == 3:
            self.add_arrows([self.ongoing_action[2]])
            try:
                self.board_delegate.perform_action(*self.ongoing_action)
            except AttributeError:
                pass
        else:
            self.undo_action()

    def perform_action(self, from_pos, to_pos, arr_pos):
        self.ongoing_action = [from_pos, to_pos, arr_pos]
        try:
            piece_item = self.pieces_graphics_items.pop(from_pos)
        except KeyError:
            return
        self.pieces_graphics_items[to_pos] = piece_item

        to_point = self.get_tile_rect(*to_pos).topLeft()
        self.moving_queen = piece_item
        self.pieces[to_pos] = self.pieces.pop(from_pos)
        AmazonsSound.shared.play_piece_move_sfx()
        PieceMoveAnimation(piece_item, to_point, finished=self.animate_action_arrow)

    def animate_action_arrow(self):
        self.show_arrow()

        arrow_dest_tile_rect = self.get_tile_rect(*self.ongoing_action[2])
        arrow_dest_point = arrow_dest_tile_rect.center()
        self.rotate_arrow_to_point(arrow_dest_point)
        try:
            self.shoot_arrow(self.ongoing_action[2], check_if_move_is_valid=False)
        except RuntimeError:
            return


    def move_piece(self, to_pos, undoing=False):
        self.can_undo_action = False

        from_pos = self.ongoing_action[1 if undoing else 0]
        self.deselect_piece()

        # changer de place
        piece_item = self.pieces_graphics_items[from_pos]
        del self.pieces_graphics_items[from_pos]
        self.pieces_graphics_items[to_pos] = piece_item

        to_point = self.get_tile_rect(*to_pos).topLeft()
        self.moving_queen = piece_item

        if not undoing and len(self.ongoing_action) == 1:
            self.ongoing_action.append(to_pos)

        self.pieces[to_pos] = self.pieces.pop(from_pos)

        AmazonsSound.shared.play_piece_move_sfx()

        PieceMoveAnimation(piece_item, to_point, finished=None if undoing else self.handle_end_queen_move_animation)

    def handle_end_queen_move_animation(self):
        # si la position de la flèche est déjà connue, pas besoin de marquer les positions possibles
        num_actions = len(self.ongoing_action)
        if not 2 <= num_actions <= 3:
            self.undo_action()
            return
        if num_actions == 2:
            self.can_shoot_arrow = True
            self.possible_moves = self.board_delegate.piece_moved(*self.ongoing_action)
            self.highlighting_reachable_tiles_under_mouse = True
            self.highlight_reachable_tiles()

        self.show_arrow()

    def show_arrow(self, rotate_on_mouse_position_change=True):
        arrow_icon = QPixmap(ARROW_ICON)
        arrow_icon = self.scale_pixmap_tile_size(arrow_icon)

        queen_rect = self.moving_queen.sceneBoundingRect()

        self.queen_arrow_graphics_item = self.addPixmap(arrow_icon)
        self.queen_arrow_graphics_item.setPos(QPointF(queen_rect.topLeft()))

        arrow_rect = self.queen_arrow_graphics_item.boundingRect()

        arrow_left_center_pt = QPointF(arrow_rect.center())
        self.queen_arrow_graphics_item.setTransformOriginPoint(arrow_left_center_pt)
        self.tracking_mouse_for_arrow_rotation = rotate_on_mouse_position_change


    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if not self.listen_mouse_click_events:
            return

        if self.ongoing_action:
            new_pos = self.get_outlined_tile_at_coord(event.scenePos())
            if new_pos is not None:
                if len(self.ongoing_action) == 1:
                    # la reine de départ est déjà sélectionnée et une nouvelle case a été sélectionnée
                    self.move_piece(new_pos)
                    return
                elif len(self.ongoing_action) == 2:
                    if not self.can_shoot_arrow:
                        return
                    # les cases de départ et arrivée sont déjà sélectionnées et une case de flèche
                    # vient d'être sélectionnée
                    self.shoot_arrow(new_pos)
                    return
            else:
                self.undo_action()

        # ne pas traiter le clic pour que Qt ne resélectionne pas la reine
        super(BoardScene, self).mousePressEvent(event)

    def highlight_reachable_tile_under_mouse(self, event):
        if not self.highlighting_reachable_tiles_under_mouse or event is None:
            self.scene_delegate.change_cursor(Qt.ArrowCursor)
            return
        tile_pos = self.get_outlined_tile_at_coord(event.scenePos())

        if self.prev_tile_under_mouse_pos == tile_pos:
            # la souris est toujours sur la même case, aucun changement à faire
            return

        if self.prev_tile_under_mouse_pos is not None:
            # remettre le marqueur qui était dans un état sélectionné à son état normal
            tile = self.possible_move_indicators_items[self.prev_tile_under_mouse_pos]
            tile.setBrush(self.POSSIBLE_MOVE_INDICATOR_COLOR)

        self.prev_tile_under_mouse_pos = tile_pos

        if tile_pos is not None:
            # the mouse is on top of a valid move tile, so highlight the indicator
            tile = self.possible_move_indicators_items[tile_pos]
            tile.setBrush(QBrush(self.POSSIBLE_MOVE_INDICATOR_COLOR_HIGHLIGHTED))
            self.scene_delegate.change_cursor(Qt.CrossCursor)
        else:
            self.scene_delegate.change_cursor(Qt.ArrowCursor)

    def set_arrow_rotation_to_mouse_position(self, event):
        mouse_pos = event.scenePos()
        self.rotate_arrow_to_point(mouse_pos)

    def rotate_arrow_to_point(self, to_point):
        arrow_queen_pos = self.moving_queen.sceneBoundingRect().center()

        # un peu de trigo pour trouver la rotation de la flèche
        offset = to_point - arrow_queen_pos
        dx, dy = offset.x(), offset.y()

        try:
            theta_rad = math.atan(dy / dx)
        except ZeroDivisionError:
            theta = 90 if dy >= 0 else -90
        else:
            theta = math.degrees(theta_rad)
            if dx < 0:
                # quadrant 2 et 3 du cercle trigonométrique
                theta += 180
        self.queen_arrow_graphics_item.setRotation(theta)

    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        super(BoardScene, self).mouseMoveEvent(event)

        if self.highlighting_reachable_tiles_under_mouse:
            self.highlight_reachable_tile_under_mouse(event)

        if self.tracking_mouse_for_arrow_rotation:
            self.set_arrow_rotation_to_mouse_position(event)

    @staticmethod
    def rescale_at_center(rect: QRectF, scale):
        rect_center = rect.center()

        rect.setSize(rect.size() * scale)
        rect.moveCenter(rect_center)




class PieceMoveAnimation(QGraphicsObject):

    def __init__(self, item, to_pos, finished=None, duration=500, easing_curve=QEasingCurve.InOutSine):
        super().__init__()

        self.item = item
        self.to_pos = to_pos
        self.duration = duration
        self.finished = finished

        self.from_pos = item.pos()

        self.pos_anim = None

        self.easing_curve = easing_curve

        self._setup_pos_anim()

    def _setup_pos_anim(self):
        self.pos_anim = QPropertyAnimation(self, b'pos')
        self.pos_anim.setDuration(self.duration)

        self.pos_anim.setStartValue(self.from_pos)
        self.pos_anim.setEndValue(self.to_pos)

        self.pos_anim.setEasingCurve(self.easing_curve)

        self.pos_anim.valueChanged.connect(self._update_pos)
        if self.finished is not None:
            self.pos_anim.finished.connect(self.finished)

        self.pos_anim.start()

    def _update_pos(self):
        self.item.setPos(self.pos_anim.currentValue())


class BoardSceneDelegate:
    def change_cursor(self, cursor):
        raise NotImplemented


class BoardDelegate:
    def piece_selected(self, coord) -> [tuple]:
        raise NotImplemented

    def piece_moved(self, from_coord, to_coord) -> [tuple]:
        raise NotImplemented

    def is_action_valid(self, queen_from, queen_to, arr) -> bool:
        raise NotImplemented

    def perform_action(self, queen_from, queen_to, arr):
        raise NotImplemented
