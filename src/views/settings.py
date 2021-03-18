from PyQt5.QtWidgets import QWidget, QFormLayout, QSlider, QComboBox, QPushButton, QFileDialog, QLabel, QMessageBox, \
    QSizePolicy
from PyQt5.QtCore import Qt, pyqtSlot
import src.views.strings as strings
from src.const import BOARDS_DIR
from os import path


class Settings(QWidget):
    VERTICAL_SPACING = 15

    def __init__(self, player_ids, on_ai_delay_changed, file_checker, curr_file=strings.NO_FILE):
        super().__init__()

        self.setWindowTitle(strings.SETTINGS)
        self.player_ids = player_ids

        # signal handlers
        self.on_ai_delay_changed = on_ai_delay_changed
        self.file_checker = file_checker

        # player settings
        self.player_combos = {}
        self.settings_form = QFormLayout()

        # board loader
        self.curr_file_status_label = QLabel(curr_file)
        self.load_file_button = None

        # AI timer row
        self.ai_delay_form_row = strings.AI_DELAY, QSlider(Qt.Horizontal)

        self.setup_ui()

    def setup_ui(self):
        """Crée l'interface des paramètres"""
        self.setup_layout()
        self.setup_player_type_selection()
        self.setup_load_game_button()

    ####
    # LAYOUT
    ####

    def setup_layout(self):
        """Configure le QLayout"""
        self.setLayout(self.settings_form)
        self.settings_form.setLabelAlignment(Qt.AlignLeading)
        self.settings_form.setVerticalSpacing(self.VERTICAL_SPACING)

        # les widgets peuvent grandir si la fenêtre s'agrandit horizontalement (e.g: le label fichier devient + grand)
        self.settings_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # l'utilisateur ne peut pas changer la taille de la fenêtre
        self.layout().setSizeConstraint(QFormLayout.SetFixedSize)

    ####
    # PLAYER SETTINGS
    ####

    def setup_player_type_selection(self):
        """Crée les deux premières lignes du formulaire pour pouvoir choisir le type de joueur (i.e.: IA, Humain)"""
        for player in [f"{strings.PLAYER} {player}" for player in self.player_ids]:
            player_selection = QComboBox()
            player_selection.addItems(strings.PLAYER_TYPES_LIST)
            player_selection.activated.connect(self.update_delay_slider_visibility)

            self.settings_form.addRow(str(player), player_selection)

            self.player_combos[player] = player_selection

    ###
    # AI DELAY SLIDER
    ####

    @property
    def slider_row_index(self):
        """Renvoie l'indice de la ligne du formulaire qui contient le slider délai IA et -1 si il ne le trouve pas"""
        slider = self.ai_delay_form_row[1]
        slider_row_index = self.settings_form.getWidgetPosition(slider)[0]

        return slider_row_index

    def update_delay_slider_visibility(self):
        slider_row_idx = self.slider_row_index
        combos = self.player_combos.values()
        is_slider_visible = slider_row_idx != -1
        if all(combo.currentText() == strings.AI_PLAYER for combo in combos):
            if not is_slider_visible:
                self.ai_delay_form_row[1].show()
                self.settings_form.insertRow(2, *self.ai_delay_form_row)
        else:
            if is_slider_visible:
                row = self.settings_form.takeRow(slider_row_idx)
                row.fieldItem.widget().hide()
                row.labelItem.widget().deleteLater()

    ####
    # LOAD GAME BUTTON
    ####

    def setup_load_game_button(self):
        self.load_file_button = QPushButton()
        self.load_file_button.clicked.connect(self.handle_load_file)
        self.update_load_file_button_label()
        self.settings_form.addRow(self.curr_file_status_label, self.load_file_button)

    def update_load_file_button_label(self):
        """
        Change le label du bouton de chargement de fichier à ``NO_FILE`` si aucun aucun fichier n'est chargé
        et à ``LOAD_ANOTHER_FILE`` sinon
        """
        if self.curr_file_status_label.text() == strings.NO_FILE:
            butt_label_text = strings.LOAD_FILE
        else:
            butt_label_text = strings.LOAD_ANOTHER_FILE
        self.load_file_button.setText(butt_label_text)

    def handle_load_file(self):

        file_path, _ = QFileDialog.getOpenFileName(self, strings.LOAD_FILE, BOARDS_DIR,
                                                   strings.BOARD_FILE_EXTENSION)
        # ignorer le cas où l'utilisateur clique sur cancel
        if file_path != '':
            if not self.file_checker(file_path):
                warning_box = QMessageBox()
                warning_box.setIcon(QMessageBox.Warning)
                warning_box.setText(strings.ERROR)
                warning_box.setText(strings.INCORRECT_FILE)
                warning_box.setDefaultButton(QMessageBox.Ok)
                warning_box.exec()
            else:
                file_name = path.split(file_path)[-1]
                self.curr_file_status_label.setText(file_name)
            self.update_load_file_button_label()
