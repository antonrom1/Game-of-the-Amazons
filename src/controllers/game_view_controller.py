from src.models.amazons import Amazons
from src.views.board_view import BoardView
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from src.views.strings import START_GAME


class GameViewController:
    def __init__(self, game: Amazons):
        self.game = game
        self.window = QWidget()
        self.window.setLayout(QVBoxLayout())

        self.start_restart_button = QPushButton(START_GAME)

        self.board_view = None
        self.init_ui()

        self.window.show()

    def init_ui(self):
        pieces = {}
        for queen, positions in enumerate(self.game.board.queens):
            pieces.update({(pos.row, pos.col): queen for pos in positions})

        self.board_view = BoardView(self.game.board.size, self.window, pieces)
        self.window.layout().addWidget(self.board_view)

        self.window.layout().addWidget(self.start_restart_button)
