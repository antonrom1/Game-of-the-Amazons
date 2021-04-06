from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QResizeEvent
from src.views.board_scene import BoardScene, BoardSceneDelegate
from src.const import MIN_TILE_SIZE

class BoardView(QtWidgets.QGraphicsView, BoardSceneDelegate):

    def __init__(self, delegate, n, parent, pieces, arrows, *args, **kwargs):
        self.board_scene = BoardScene(self, delegate, n, parent)
        super().__init__(self.board_scene, *args, **kwargs)

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.setMinimumSize(*(MIN_TILE_SIZE * n,) * 2)
        self.n = n

        self.board_scene.add_pieces(pieces)
        self.board_scene.add_arrows(arrows)
        self.board_scene.redraw(n, self.rect())

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setMouseTracking(True)

        # rendre l'arrière-plan transparent
        self.setStyleSheet("background-color: transparent")

    def sizeHint(self):
        return self.minimumSize() * 3

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.board_scene.resize(self.rect())

    def change_cursor(self, cursor):
        self.setCursor(cursor)

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        # il ne faut pas que l'utilisateur puisse déplacer le plateau...
        pass
