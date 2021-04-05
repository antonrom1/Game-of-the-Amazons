from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSizePolicy
from src.views.board_view import BoardView
from src.views import const_strings


class MainWindow(QWidget):
    def __init__(self, board_view: BoardView):
        super().__init__()
        self.setWindowTitle(const_strings.APP_NAME)

        self.board_view = board_view
        self.board_section_widget = QWidget()
        self.sidebar = QWidget()

        self.setup_ui()

    def setup_ui(self):
        v_layout = QVBoxLayout()
        self.setLayout(v_layout)

        self.setup_board_section()

        self.layout().addWidget(QPushButton(const_strings.START_GAME))

    def setup_board_section(self):

        self.board_section_widget.setLayout(QHBoxLayout())
        self.layout().addWidget(self.board_section_widget)

        self.sidebar = QWidget()
        self.sidebar.setLayout(QVBoxLayout())
        self.sidebar.setSizePolicy(QSizePolicy.GrowFlag | QSizePolicy.ExpandFlag, QSizePolicy.GrowFlag | QSizePolicy.ExpandFlag)
        self.sidebar.layout().addWidget(QPushButton('aa'))

        self.board_section_widget.layout().addWidget(self.board_view)
        self.board_section_widget.layout().addWidget(self.sidebar)



