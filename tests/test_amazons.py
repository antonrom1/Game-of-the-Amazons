import unittest
from src.amazons import Amazons
from src.player import Player
from contextlib import redirect_stdout
from io import StringIO


class TestAmazons(unittest.TestCase):
    def test_endgame_detection(self):
        tests = [
            'ressources/plateau_6.txt'
        ]
        with redirect_stdout(StringIO()):
            for board_file in tests:
                game = Amazons(board_file)
                self.assertEqual(Player.BLACK, game.winner)

    def test_minimax(self):
        tests = [
            'ressources/plateau_8.txt'
        ]
        with redirect_stdout(StringIO()):
            for board_file in tests:
                game = Amazons(board_file, white_opens=False)
                game.play()
                self.assertEqual(Player.BLACK, game.winner)



if __name__ == "__main__":
    unittest.main()
