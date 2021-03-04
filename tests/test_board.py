import unittest
from src.board import Board
from src.geometry import Coord
from src.cell import Piece
from src.player import Player


class TestBoard(unittest.TestCase):

    def test_pieces_positions(self):
        # les coordonnées ne sont pas uniques
        self.assertRaises(ValueError, Board, [Coord((1, 1)), Coord((1, 2))], [Coord((1, 1))], [], size=4)
        # pas de reines blanches
        self.assertRaises(ValueError, Board, [Coord((1, 1))], [], [])
        # une reine qui n'est pas dans le plateau
        self.assertWarns(UserWarning, Board, [Coord((1, 1))], [Coord((1, 9))], [], size=9)
        self.assertWarns(UserWarning, Board, [Coord((1, 1))], [Coord((1, -1))], [], size=4)

        # vérifier que les positions se sauvegardent correctement dans Board
        valid_positions = [
            [Coord((1, 1)), Coord((2, 1)), Coord((3, 1)), Coord((4, 1))],
            [Coord((1, 4)), Coord((2, 4)), Coord((3, 4)), Coord((4, 4))],
            []
        ]

        board = Board(*valid_positions)
        self.assertEqual(set(board.get_positions(Piece.WHITE)), set(valid_positions[1]))
        self.assertEqual(set(board.get_positions(Piece.BLACK)), set(valid_positions[0]))

    def test_size(self):
        size = 4
        board = Board([Coord((1, 1))], [Coord((1, 2))], [], size=size)
        self.assertEqual(size, board.size)

    def test_possible_moves(self):
        bd = Board([Coord((3, 3)), Coord((0, 1))], [Coord((3, 5)), Coord((0, 3))],
                   [Coord((1, 5)), Coord((4, 5)), Coord((5, 5)), Coord((1, 4)), Coord((3, 4)), Coord((5, 4)),
                    Coord((1, 3)), Coord((2, 3)), Coord((5, 3)), Coord((1, 2)), Coord((2, 2)), Coord((4, 2)),
                    Coord((5, 2)), Coord((1, 1)), Coord((2, 1)), Coord((3, 1)), Coord((5, 1)), Coord((2, 0)),
                    Coord((5, 0))],
                   size=6)

        tests = [
            [Coord((3, 3)), {Coord((3, 2)), Coord((4, 3)), Coord((4, 4)), Coord((2, 4))}],
            [Coord((3, 5)), {Coord((4, 4)), Coord((2, 5)), Coord((2, 4))}],
            [Coord((0, 3)), {Coord((0, 5)), Coord((0, 4)), Coord((0, 2))}],
            [Coord((0, 1)), {Coord((0, 2)), Coord((0, 0)), Coord((1, 0))}]
        ]

        for source, moves_test in tests:
            self.assertEqual(moves_test, set(bd.possible_moves(source)))

    def test_count_remaining_moves(self):
        tests = [
            [5, None],
            [6, {Player.WHITE: 3, Player.BLACK: 9}],
            [7, {Player.WHITE: 11, Player.BLACK: 9}]
        ]
        for board_num, moves in tests:
            bd = Board.load_board(f'ressources/plateau_{board_num}.txt')
            self.assertEqual(bd.count_remaining_moves(), moves)

    def test_str(self):
        tests = [
            [1, "6  . ● . . ● .\n5  . . ● . . .\n4  . . . . . .\n3  . . . . . .\n2  . . . ○ . .\n1  . ○ . . ○ .\n"
                "   a b c d e f"],
            [2, "6  . ● . . ● .\n5  . . ● . . X\n4  . . . . . .\n3  . . . . . .\n2  . . . ○ . .\n1  . ○ . . ○ X\n"
                "   a b c d e f"]
        ]

        for board_num, bd_str in tests:
            bd = Board.load_board(f'ressources/plateau_{board_num}.txt')
            self.assertEqual(str(bd), bd_str)

    def test_copy(self):
        bd1 = Board.default_board()
        bd2 = bd1.copy()
        bd2_black = bd2.get_positions(Piece.BLACK)
        bd2_white = bd2.get_positions(Piece.WHITE)
        bd2.swap_pieces(bd2_black[0], bd2_white[0])
        self.assertNotEqual(bd2.get_positions(Piece.WHITE), bd1.get_positions(Piece.WHITE))


if __name__ == "__main__":
    unittest.main()
