from sys import argv
from os.path import isfile

from src.amazons import Amazons
from src.players import AIPlayer
from src.const import PLAYER_1, PLAYER_2

def check_file():
    if len(argv) < 2:
        print('Usage: python3 partie3.py <path>')
        return False
    if not isfile(argv[1]):
        print(f'{argv[1]} n\'est pas un chemin valide vers un fichier')
        return False
    return True

def main():
    if not check_file():
        return
    game = Amazons(argv[1])
    game.players = AIPlayer(game.board, PLAYER_1, 1, 2), AIPlayer(game.board, PLAYER_2, 1, 2)
    game.play()


if __name__ == '__main__':
    import random
    random.seed(0xCAFE)
    main()
