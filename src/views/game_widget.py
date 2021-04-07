from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSizePolicy, QMessageBox, QLabel
from src.views.board_view import BoardView
from src.views import const_strings
from src.views.sound import AmazonsSound, AmazonsSoundDelegate
from src.views.toggle_image_button import ToggleImageButton
from PyQt5.QtCore import Qt
from src.const import NO_MUSIC_ICON, MUSIC_ICON, ICONS_WIDTH
from functools import lru_cache


class GameWidgetDelegate:
    def restart_game(self):
        pass

    def create_new_game(self):
        pass

    def view_will_unload(self):
        pass

class GameWidget(QWidget, AmazonsSoundDelegate):
    def __init__(self, board_view: BoardView, delegate: GameWidgetDelegate):
        super().__init__()

        AmazonsSound.shared.add_delegate(self)

        self.setWindowTitle(const_strings.APP_NAME)

        self.board_view = board_view
        self.board_section_widget = QWidget(self)
        self.sidebar = QWidget()
        self.delegates = [delegate]
        self.restart_game_btn = None
        self.music_button = None
        self.current_turn_indicator = None
        self.will_unload = False

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setup_ui()

    def add_delegate(self, delegate):
        self.delegates.append(delegate)

    def setup_ui(self):
        v_layout = QVBoxLayout(self)
        self.setLayout(v_layout)

        self.setup_board_section()

        self.setup_current_turn_indicator()
        self.setup_music_button()
        self.setup_restart_btn()
        self.setup_new_game_button()

    def setup_board_section(self):
        self.board_section_widget.setLayout(QHBoxLayout())
        self.layout().addWidget(self.board_section_widget)

        self.sidebar = QWidget()
        self.sidebar.setLayout(QVBoxLayout())
        self.sidebar.setSizePolicy(QSizePolicy.GrowFlag | QSizePolicy.ExpandFlag, QSizePolicy.GrowFlag | QSizePolicy.ExpandFlag)

        self.board_section_widget.layout().addWidget(self.board_view)
        self.board_section_widget.layout().addWidget(self.sidebar)

    def setup_new_game_button(self):
        new_game_button = QPushButton(const_strings.NEW_GAME)
        self.sidebar.layout().addWidget(new_game_button)
        new_game_button.clicked.connect(self.new_game)

    def setup_music_button(self):
        self.music_button = ToggleImageButton(MUSIC_ICON, NO_MUSIC_ICON, AmazonsSound.shared.is_music_playing)
        self.sidebar.layout().addWidget(self.music_button)
        self.music_button.clicked.connect(self.handle_music_switched)

    def setup_restart_btn(self):
        self.restart_game_btn = QPushButton(const_strings.RESTART_GAME)
        self.sidebar.layout().addWidget(self.restart_game_btn)
        self.restart_game_btn.clicked.connect(self.restart_game)

    def setup_current_turn_indicator(self):
        current_turn_indicator_container = QWidget()
        self.sidebar.layout().addWidget(current_turn_indicator_container)

        current_turn_indicator_container.setLayout(QHBoxLayout())

        self.current_turn_indicator = QLabel()
        current_turn_indicator_label = QLabel(const_strings.CURRENT_TURN)

        current_turn_indicator_container.layout().addWidget(current_turn_indicator_label)
        current_turn_indicator_container.layout().addWidget(self.current_turn_indicator)

    def update_current_turn_indicator(self, image_path):
        pixmap = self.get_scaled_pixmap(image_path)
        self.current_turn_indicator.setPixmap(pixmap)

    @lru_cache()
    def get_scaled_pixmap(self, image_path):
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaledToWidth(ICONS_WIDTH, Qt.SmoothTransformation)
        return pixmap

    def replace_board_view(self, new_board_view):
        self.board_section_widget.layout().replaceWidget(self.board_view, new_board_view)
        self.board_view.deleteLater()
        self.board_view = new_board_view

    def close(self) -> None:
        self.will_unload = True
        for delegate in self.delegates:
            delegate.view_will_unload()
        AmazonsSound.shared.remove_delegate(self)
        super(GameWidget, self).close()

    def new_game(self):
        # ask the user if he is ok to lose the current game status
        mess_box = QMessageBox()
        mess_box.setIcon(QMessageBox.Warning)
        mess_box.setText(const_strings.YOU_WILL_LOSE_CURR_GAME)

        mess_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        mess_box.setDefaultButton(QMessageBox.No)

        if mess_box.exec() == QMessageBox.Yes:
            self.music_button.setChecked(False)
            self.handle_music_switched()
            self.create_new_game()

    def exhibit_game_over(self, winner):
        mess_box = QMessageBox(self)
        mess_box.setIcon(QMessageBox.Information)
        mess_box.setText(const_strings.PLAYER_WON_MESS.format(winner))
        mess_box.setStandardButtons(QMessageBox.Ok)
        mess_box.exec_()

    def restart_game(self):
        for delegate in self.delegates:
            delegate.restart_game()

    def create_new_game(self):
        for delegate in self.delegates:
            delegate.create_new_game()

    def handle_music_switched(self):
        if self.music_button.isChecked():
            AmazonsSound.shared.play_music()
        else:
            AmazonsSound.shared.stop_music()

    def music_started_playing(self):
        self.music_button.setChecked(True)

    def music_stopped_playing(self):
        self.music_button.setChecked(False)

