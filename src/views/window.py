from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSizePolicy, QMessageBox
from src.views.board_view import BoardView
from src.views import const_strings
from src.views.sound import AmazonsSound, AmazonsSoundDelegate
from PyQt5.QtGui import QIcon
from src.views.toggle_image_button import ToggleImageButton
from src.const import NO_MUSIC_ICON, MUSIC_ICON


class GameWidgetDelegate:
    def restart_game(self):
        raise NotImplemented

class GameWidget(QWidget, AmazonsSoundDelegate):
    def __init__(self, board_view: BoardView, delegate: GameWidgetDelegate):
        super().__init__()

        AmazonsSound.shared.add_delegate(self)

        self.setWindowTitle(const_strings.APP_NAME)

        self.board_view = board_view
        self.board_section_widget = QWidget(self)
        self.sidebar = QWidget()
        self.delegate = delegate
        self.restart_game_btn = None
        self.music_button = None

        self.setup_ui()

    def setup_ui(self):
        v_layout = QVBoxLayout(self)
        self.setLayout(v_layout)

        self.setup_board_section()
        self.setup_restart_btn()
        self.setup_music_button()

    def setup_board_section(self):
        self.board_section_widget.setLayout(QHBoxLayout())
        self.layout().addWidget(self.board_section_widget)

        self.sidebar = QWidget()
        self.sidebar.setLayout(QVBoxLayout())
        self.sidebar.setSizePolicy(QSizePolicy.GrowFlag | QSizePolicy.ExpandFlag, QSizePolicy.GrowFlag | QSizePolicy.ExpandFlag)

        self.board_section_widget.layout().addWidget(self.board_view)
        self.board_section_widget.layout().addWidget(self.sidebar)

    def setup_music_button(self):
        self.music_button = ToggleImageButton(MUSIC_ICON, NO_MUSIC_ICON, AmazonsSound.shared.is_music_playing)
        self.sidebar.layout().addWidget(self.music_button)
        self.music_button.clicked.connect(self.handle_music_switched)

    def setup_restart_btn(self):
        self.restart_game_btn = QPushButton(const_strings.RESTART_GAME)
        self.sidebar.layout().addWidget(self.restart_game_btn)
        self.restart_game_btn.clicked.connect(self.delegate.restart_game)

    def replace_board_view(self, new_board_view):
        self.board_section_widget.layout().replaceWidget(self.board_view, new_board_view)
        self.board_view.deleteLater()
        self.board_view = new_board_view

    def exhibit_game_over(self, winner):
        mess_box = QMessageBox(self)
        mess_box.setIcon(QMessageBox.Information)
        mess_box.setText(const_strings.PLAYER_WON_MESS.format(winner))
        mess_box.setStandardButtons(QMessageBox.Ok)
        mess_box.exec_()

    def handle_music_switched(self):
        if self.music_button.isChecked():
            AmazonsSound.shared.play_music()
        else:
            AmazonsSound.shared.stop_music()

    def music_started_playing(self):
        self.music_button.setChecked(True)

    def music_stopped_playing(self):
        self.music_button.setChecked(False)

