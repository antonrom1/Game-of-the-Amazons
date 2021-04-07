from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.const import *
from src.views.const_strings import APP_NAME


class AmazkombatApp(QApplication):
    def __init__(self):
        super().__init__([APP_NAME])
        self.setApplicationName(APP_NAME)

        # Load icon
        self.setWindowIcon(QIcon(APP_ICON))


