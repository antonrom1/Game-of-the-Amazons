"""
Prénom:     Anton
Nom:        ROMANOVA
Matricule:  521935
"""

from src.models.pos2d import Vec2D
from os.path import join

WHITE = '\u25CB'  # caractère du joueur blanc
BLACK = '\u25CF'  # caractère du joueur noir

INF = float('inf')

PLAYER_1 = 0
PLAYER_2 = 1
EMPTY = 2
ARROW = 3

PLAYERS = [PLAYER_1, PLAYER_2]

WIN = 100000
DRAW = 0
# LOSS = -WIN

AI_AI_DELAY_MINMAX_MILLIS = (2000, 10000)
AI_AI_DELAY_DEFAULT_MILLIS = 2000

NORTH =      (1, 0)
NORTH_EAST = (1, 1)
EAST =       (0, 1)
SOUTH_EAST = (-1, 1)
SOUTH =      (-1, 0)
SOUTH_WEST = (-1, -1)
WEST =       (0, -1)
NORTH_WEST = (1, -1)
DIRECTIONS = (NORTH, NORTH_EAST, EAST, SOUTH_EAST, SOUTH, SOUTH_WEST, WEST, NORTH_WEST)
DIRECTIONS = tuple(Vec2D(*direction) for direction in DIRECTIONS)  # tuple des 8 directions (inter)cardinales

#       PLAYER_1  PLAYER_2  EMPTY  ARROW
CHARS = [WHITE,   BLACK,    '.',   'X']

ERREUR_COUP = "Format du coup non valide"
ERREUR_REINE = "Pas de reine à la position de départ"
ERREUR_CHEMIN = "Le coup n'est pas valide, soit parce qu'il ne respecte pas les règles du jeu d'échec, soit parce que " \
                "le chemin est occupé"
MESSAGE_COUP = "Joueur {}, donnez un coup de format 'position reine avant > position reine après > position flèche' " \
               "(ex : a7>b7>a8) >> "


###############
# GUI
###############

# BOARD
DEFAULT_TILE_COLORS = ["af3232", "ffd7c8"]
MIN_TILE_SIZE = 25

# ASSETS

# Pour que les Unix-like (MacOS, Linux) et Windows soient compatibles
RESSOURCES_DIR = join('./ressources')
ASSETS_DIR = join(RESSOURCES_DIR, 'assets')
ICONS_DIR = join(ASSETS_DIR, 'icons')
BOARDS_DIR = join(RESSOURCES_DIR, 'boards')

APP_ICON = join(ICONS_DIR, 'app_icon.svg')

QUEENS_ICONS_FILENAMES = 'wq.png', 'bq.png'
QUEEN_ICONS = [join(ICONS_DIR, filename) for filename in QUEENS_ICONS_FILENAMES]

ARROW_ICON = join(ICONS_DIR, 'arrow.png')

MUSIC_ICON = join(ICONS_DIR, 'music-note.png')
NO_MUSIC_ICON = join(ICONS_DIR, 'no_music_note.png')


SOUND_DIR = join(ASSETS_DIR, 'sounds')

ARROW_SFX = join(SOUND_DIR, 'arrow.wav')
PIECE_SLIDE_SFX = join(SOUND_DIR, 'piece_slide.wav')
RICKROLL = join(SOUND_DIR, 'Rick Astley - Never Gonna Give You Up (Video).wav')
SOUNDTRACK = join(SOUND_DIR, 'Richard Wagner - Ride Of The Valkyries.wav')

REACHABLE_INDICATOR_SIZE_TO_TILE_SIZE_RATIO = 0.2
ICONS_WIDTH = 50
