from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPixmap, QResizeEvent, QPaintEvent, QIcon
from PyQt5.QtCore import QSize


class ToggleImageButton(QPushButton):
    def __init__(self, active_state_image_path, inactive_state_image_path, default_state):
        super(ToggleImageButton, self).__init__()

        self._active_icon = QIcon(QPixmap(active_state_image_path))
        self._inactive_icon = QIcon(QPixmap(inactive_state_image_path))

        self.setCheckable(True)
        self.setChecked(default_state)

    def _get_icon_for_current_state(self):
        if self.isChecked():
            return self._active_icon
        else:
            return self._inactive_icon

    def update_icon(self):
        self.setIcon(self._get_icon_for_current_state())
        self.setIconSize(QSize(25, 25))

    @property
    def current_state(self):
        return self._current_state

    def checkStateSet(self) -> None:
        super(ToggleImageButton, self).checkStateSet()
        self.update_icon()

