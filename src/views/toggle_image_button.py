"""
Prénom:     Anton
Nom:        ROMANOVA
Matricule:  521935
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize


class ToggleImageButton(QPushButton):
    """Un toggle avec une image pour chaque état possible"""
    def __init__(self, active_state_image_path, inactive_state_image_path, default_state):
        super(ToggleImageButton, self).__init__()

        self._active_icon = QIcon(QPixmap(active_state_image_path))
        self._inactive_icon = QIcon(QPixmap(inactive_state_image_path))

        self.setCheckable(True)
        self.setChecked(default_state)

    def _get_icon_for_current_state(self):
        # renvoie l'image en fonction de l'état actuel
        if self.isChecked():
            return self._active_icon
        else:
            return self._inactive_icon

    def update_icon(self):
        """Met à jour l'image du toggle"""
        self.setIcon(self._get_icon_for_current_state())
        self.setIconSize(QSize(25, 25))

    def checkStateSet(self) -> None:
        """Met l'image du toggle à jour lorsque l'état du toggle est changé"""
        super(ToggleImageButton, self).checkStateSet()
        self.update_icon()

