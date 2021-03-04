"""
Nom:            ROMANOVA
Prénom:         Anton
Matricule:      521935
Section:        BA1-INFO
"""

from src import amazons
from sys import argv
from src.ask_user import ask_user_bool


def main():
    game_file = None
    if len(argv) > 1:
        game_file = argv[1]
    game = amazons.Amazons(board=game_file, use_ai=ask_user_bool("Voulez-vous jouer contre une IA"))
    try:
        game.play()
    except KeyboardInterrupt:
        print("\nMerci d'avoir joué, au revoir!")
        exit()


if __name__ == "__main__":
    main()
