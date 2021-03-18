from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QIcon
from src.const import *
from src.views.strings import APP_NAME
from src.views.settings import Settings


class AmazkombatApp(QApplication):
    def __init__(self):
        super().__init__([APP_NAME])
        self.setApplicationName(APP_NAME)

        # Load icon
        self.setWindowIcon(QIcon(APP_ICON))


if __name__ == "__main__":
    AmazkombatApp().exec_()

