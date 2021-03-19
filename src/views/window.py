from PyQt5.QtWidgets import QSlider, QFormLayout, QGroupBox, QVBoxLayout, QPushButton, QWidget, QComboBox, QFileDialog, QApplication
from PyQt5.QtCore import Qt
from src.views.board_view import BoardView
import src.views.strings as strings


class MainWindow(QWidget):
    def __init__(self, board_view: BoardView):
        super().__init__()
        self.setWindowTitle(strings.APP_NAME)
        self.board_view = board_view
        self.setup_ui()

    def setup_ui(self):
        v_layout = QVBoxLayout()
        self.setLayout(v_layout)

        self.setup_board()

        self.layout().addWidget(QPushButton(self.START_GAME_BUTTON_TEXT))

    def setup_board(self):
        self.layout().addWidget(self.board_view)

