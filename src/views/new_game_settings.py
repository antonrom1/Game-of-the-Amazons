from PyQt5.QtWidgets import QWidget, QFormLayout, QSlider, QComboBox, QPushButton, QFileDialog, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from src.views import const_strings
from src.const import BOARDS_DIR, AI_AI_DELAY_MINMAX_MILLIS, AI_AI_DELAY_DEFAULT_MILLIS
from os import path


class NewGameSettings(QWidget):
    """Fenêtre de configuration de nouveau jeu"""
    VERTICAL_SPACING = 15

    def __init__(self, delegate, player_ids, ai_ai_delay=AI_AI_DELAY_DEFAULT_MILLIS, curr_file_path=const_strings.NO_FILE):
        super().__init__()
        self.player_ids = player_ids

        assert isinstance(delegate, NewGameSettingsDelegate)
        self.delegate = delegate

        # player settings
        self.player_combos = {}
        self.settings_form = None

        # board loader
        self.load_file_button = None
        self.remove_board_button = None
        self.board_file_path = curr_file_path
        filename = path.split(curr_file_path)[-1]
        self.curr_file_status_label = QLabel(filename)

        # AI timer row
        self.ai_ai_delay = ai_ai_delay
        self.ai_ai_slider = QSlider(Qt.Horizontal)
        self.ai_ai_delay_form_row = const_strings.AI_DELAY, self.ai_ai_slider

        # Save cancel
        self.save_button = None

        # UI
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface du widget"""
        self.setup_window()
        self.setup_layout()

        self.setup_player_type_selection()
        self.setup_ai_ai_slider()

        self._add_sep_row()
        self.setup_load_game_row()

        self._add_sep_row()
        self.setup_save_cancel_buttons()

        self.disable_enable_buttons()

    def disable_enable_buttons(self):
        """Désactive les boutons "Appliquer" et "Supprimer" si il n'y a aucun fichier et les active sinon"""
        is_file_defined = self.is_file_defined

        # pour Qt, setDisabled(True) active le bouton et setDisabled(False) le désactive
        self.remove_board_button.setDisabled(not is_file_defined)
        self.save_button.setDisabled(not is_file_defined)

    def setup_window(self):
        """Configure la fenêtre"""
        self.setWindowTitle(const_strings.SETTINGS)

    ####
    # LAYOUT
    ####

    def setup_layout(self):
        """Configure le layout"""
        self.settings_form = QFormLayout()
        self.setLayout(self.settings_form)

        self.settings_form.setLabelAlignment(Qt.AlignLeading)
        self.settings_form.setVerticalSpacing(self.VERTICAL_SPACING)
        self.settings_form.setRowWrapPolicy(QFormLayout.WrapLongRows)

        # les widgets peuvent grandir si la fenêtre s'agrandit horizontalement (e.g: le label fichier devient + grand)
        self.settings_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # l'utilisateur ne peut pas changer la taille de la fenêtre
        self.layout().setSizeConstraint(QFormLayout.SetFixedSize)

    ####
    # PLAYER SETTINGS
    ####

    def setup_player_type_selection(self):
        """Crée les deux premières lignes du formulaire pour pouvoir choisir le type de joueur (i.e.: IA, Humain)"""
        for player in [f"{const_strings.PLAYER} {player}" for player in self.player_ids]:
            player_selection = QComboBox()
            player_selection.addItems(const_strings.PLAYER_TYPES_LIST)
            player_selection.activated.connect(self.update_delay_slider_visibility)

            self.settings_form.addRow(str(player), player_selection)

            self.player_combos[player] = player_selection

    ###
    # AI DELAY SLIDER
    ####

    def setup_ai_ai_slider(self):
        """Crée le slider ai_ai"""
        min_delay, max_delay = AI_AI_DELAY_MINMAX_MILLIS

        self.ai_ai_slider.setMinimum(min_delay)
        self.ai_ai_slider.setMaximum(max_delay)

        self.ai_ai_slider.setValue(self.ai_ai_delay)

        self.ai_ai_slider.valueChanged.connect(self.handle_ai_ai_delay_slider_value_change)

    @property
    def is_mode_ai_ai(self):
        """Renvoie si les deux joueurs sont mis à AI"""
        return all(combo.currentText() == const_strings.AI_PLAYER for combo in self.player_combos.values())

    @property
    def slider_row_index(self):
        """
        Renvoie l'indice de la ligne du formulaire qui contient le slider délai IA et -1 si il ne le trouve pas
        """
        slider = self.ai_ai_delay_form_row[1]
        slider_row_index = self.settings_form.getWidgetPosition(slider)[0]

        return slider_row_index

    def update_delay_slider_visibility(self):
        """
        Cache le slider délai IA si les deux joueurs ne sont pas mis à IA et l'affiche dans le cas contraire
        """
        slider_row_idx = self.slider_row_index  # ligne du slider dans le formulaire & -1 si il n'y est pas
        combos = self.player_combos.values()  # les joueurs (IA, Humain) que l'utilisateur a choisi

        is_slider_visible = slider_row_idx != -1

        if self.is_mode_ai_ai:
            # tous les joueurs sont mis à IA
            if not is_slider_visible:
                # Affiche le slider s'il ne l'est pas déjà
                self.ai_ai_delay_form_row[1].show()
                self.settings_form.insertRow(2, *self.ai_ai_delay_form_row)
        else:
            # les joueurs ne sont pas tous à IA
            if is_slider_visible:
                # Cache le slider s'il ne l'est pas déjà
                row = self.settings_form.takeRow(slider_row_idx)
                row.fieldItem.widget().hide()
                row.labelItem.widget().deleteLater()

    def handle_ai_ai_delay_slider_value_change(self, new_val):
        self.ai_ai_delay = new_val

    ####
    # LOAD GAME BUTTON
    ####

    @property
    def is_file_defined(self):
        """Renvoie si le fichier de jeu est défini"""
        return self.curr_file_status_label.text() != const_strings.NO_FILE

    def setup_load_game_row(self):
        """Configure la ligne du formulaire avec le bouton pour charger un fichier un plateau"""
        self.load_file_button = QPushButton()
        self.remove_board_button = QPushButton()

        self.load_file_button.clicked.connect(self.handle_load_file)

        self.remove_board_button.setText(const_strings.REMOVE)
        self.remove_board_button.clicked.connect(self.handle_delete_file)

        self.update_load_file_button_label()

        # pour éviter que des noms de fichiers (très) longs rendent la fenêtre excessivement grande
        self.curr_file_status_label.setWordWrap(True)

        self.settings_form.addRow(self.load_file_button, self.remove_board_button)
        self.settings_form.addRow(self.curr_file_status_label)

    def update_load_file_button_label(self):
        """
        Change le label du bouton de chargement de fichier à ``NO_FILE`` si aucun aucun fichier n'est chargé
        et à ``LOAD_ANOTHER_FILE`` sinon
        """
        if self.is_file_defined:
            butt_label_text = const_strings.LOAD_ANOTHER_FILE
        else:
            butt_label_text = const_strings.LOAD_FILE
        self.load_file_button.setText(butt_label_text)

    def handle_load_file(self):
        """
        Affiche un file dialog et vérifie si le fichier choisi est bien un fichier de plateau avec la fonction
        externe: file_checker
        Met à jour le label avec le nom du fichier si le fichier est correct
        """
        file_path, _ = QFileDialog.getOpenFileName(self, const_strings.LOAD_FILE, BOARDS_DIR,
                                                   const_strings.BOARD_FILE_EXTENSION)

        if file_path.strip():  # ignorer le cas où l'utilisateur clique sur cancel
            if not self.delegate.is_board_file_valid(file_path):
                # fichier non valide
                # prévenir l'utilisateur que le fichier n'est pas correct
                self._warn(const_strings.INCORRECT_FILE)
            else:  # fichier valide
                self.board_file_path = file_path

                # mettre le texte du label au nom du fichier
                file_name = path.split(file_path)[-1]
                self.curr_file_status_label.setText(file_name)

                self.disable_enable_buttons()
            self.update_load_file_button_label()


    def handle_delete_file(self):
        """Enlève le fichier de jeu de l'interface"""
        self.curr_file_status_label.setText(const_strings.NO_FILE)
        self.disable_enable_buttons()
        self.update_load_file_button_label()

        self.board_file_path = None

    ####
    # SAVE CHANGES
    ####

    def setup_save_cancel_buttons(self):
        """Crée les boutons de sauvegarde et d'annulation"""
        self.save_button = QPushButton(const_strings.SAVE)
        self.save_button.setDefault(True)
        cancel_button = QPushButton(const_strings.CANCEL)

        cancel_button.clicked.connect(self.handle_cancel)
        self.save_button.clicked.connect(self.handle_save)

        self.settings_form.addRow(cancel_button, self.save_button)

    def handle_cancel(self):
        """Ferme le programme"""
        self.close()

    def _add_sep_row(self):
        """Ajoute une ligne de séparation"""
        self.settings_form.addRow('', QLabel())

    def handle_save(self):
        """Renvoie les paramètres de jeu à l'observateur"""
        if self.board_file_path != const_strings.NO_FILE:
            board = path.abspath(self.board_file_path)
        else:
            board = None

        if self.is_mode_ai_ai:
            delay = self.ai_ai_delay / 1000  # pour avoir des secondes, et pas des millisecondes
        else:
            delay = None

        players = [combo.currentText() for combo in self.player_combos.values()]

        succ = self.delegate.save_settings(board, players, delay)

        if succ:
            self.close()
        else:
            self._warn(const_strings.SAVE_SETTINGS_ERROR)

    ####
    # WARNING
    ####

    @staticmethod
    def _warn(mess, buttons=QMessageBox.Ok):
        # crée un message d'erreur
        # mess est un string
        warning_box = QMessageBox()
        warning_box.setIcon(QMessageBox.Warning)
        warning_box.setText(mess)
        warning_box.setStandardButtons(buttons)
        warning_box.exec()


class NewGameSettingsDelegate:
    """Protocole pour les observateurs de NewGameSettings"""
    def is_board_file_valid(self, file_path) -> bool:
        """Est appelé pour vérifier si le fichier de jeu est valide"""
        raise NotImplemented

    def save_settings(self, file_path, players_str, ai_ai_delay) -> bool:
        """Renvoie les paramètres pour le nouveau jeu"""
        raise NotImplemented
