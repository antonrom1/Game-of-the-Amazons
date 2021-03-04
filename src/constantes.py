WHITE_CHAR = '\u25CB'
BLACK_CHAR = '\u25CF'
ARROW_CHAR = 'X'
EMPTY_CHAR = '.'

SPACES_ROW_NUM = 3
COL_SEP = " "
ROW_SEP = "\n"
INPUT_SEPARATOR = ">"

BLACK_DEFAULT_POS = ["a7", "d10", "g10", "j7"]
WHITE_DEFAULT_POS = ["a4", "d1", "g1", "j4"]

GAME_FILE_SEPARATOR = ","

LETTERS_IN_ALPHABET = 26

INPUT_ERR = "Format du coup non valide"
QUEEN_ERR = "Pas de reine à la position de départ"
PATH_ERR = "Le coup n'est pas valide, soit parce qu'il ne respecte pas les règles du jeu d'échec, soit parce que "\
                "le chemin est occupé"
INPUT_MESS = "Joueur {}, donnez un coup de format 'position reine avant > position reine après > position flèche' " \
               "(ex : a7>b7>a8) >> "
