import unittest
from src.geometry import Coord, Line, Hull


import unittest
from src.geometry import Coord


class TestCoord(unittest.TestCase):

    def test_tuple_from_str(self):
        test_cases = [('e1', (4, 0)), ('f7', (5, 6)), ('a1', (0, 0))]
        for test, sol in test_cases:
            self.assertEqual(Coord.tuple_from_str(test), sol)

    def test_to_str(self):
        test_cases = [((4, 0), 'e1'), ((5, 6), 'f7'), ((0, 0), 'a1')]
        for test, sol in test_cases:
            self.assertEqual(str(Coord(test)), sol)

    def test_in_board(self):
        test_cases = [('d1', 3, False), ('c1', 3, True), ('f7', 10, True), ('a1', 8, True), ((-1, 1), 4, False)]
        for test, size, valid in test_cases:
            self.assertEqual(Coord(test).in_board(size), valid)

    def test_add(self):
        self.assertEqual(Coord('d5') + (2, 2), Coord((5, 6)))
        self.assertEqual(Coord((1, 1)) + (-2, 2), Coord((-1, 3)))

    def test_distance_sq(self):
        tests = [
            [(1, 1), (2, 2), 2],
            [(-1, 6), (2, 0), 45],
            [(-1, 2), (21, 3), 485],
            [(-1, 2), (0, 2), 1],
            [(0, 2), (0, 7), 25],
        ]
        for p1, p2, dist_sq in tests:
            self.assertEqual(dist_sq, Coord(p1).distance_sq(Coord(p2)))


class TestLine(unittest.TestCase):

    def test_equal_lines(self):
        tests = [
            [(1, 1, 1), (1, 1, 1), True],
            [(1, 1, 1), (2, 2, 2), True],
            [(1, 1, 1), (-5, -5, -5), True],
            [(1, 1, 0), (2, 2, 2), False],
            [(1, 2, 3), (-5, -10, -15), True]
        ]

        for l1, l2, equal in tests:
            if equal:
                self.assertEqual(Line(*l1), Line(*l2))
            else:
                self.assertNotEqual(Line(*l1), Line(*l2))

    def tests_special_cases(self):
        self.assertRaises(ValueError, Line, 0, 0, 0)
        self.assertTrue(Line(1, 0, 0).is_vertical)
        self.assertFalse(Line(0, 1, 0).is_vertical)
        self.assertFalse(Line(1, 1, 0).is_vertical)
        self.assertTrue(Line(0, 1, 0).is_horizontal)
        self.assertFalse(Line(1, 1, 0).is_horizontal)
        self.assertFalse(Line(1, 1, 0).is_horizontal)

    def test_through_points(self):
        tests = [
            [(1, 2), (2, 1), (1, 1, -3)],
            [(375, 12), (1280, 24), (-12, 905, -6360)],
            [(5, 6), (-1, 7), (1, 6, -41)],
            [(-2, -5), (-1, 4), (-9, 1, -13)]
        ]
        for p1, p2, line in tests:
            self.assertEqual(Line(*line), Line.through_two_points(p1, p2))

        self.assertRaises(ValueError, Line.through_two_points, Coord((1, 1)), Coord((1, 1)))

    def test_perpendicular_lines(self):
        tests = [
            [(3, 9, 1), (9, -3, 12), (0, 4)]
        ]

        for line, perpend, pt in tests:
            self.assertEqual(Line(*perpend), Line(*line).perpendicular(Coord(pt)))

    def test_split_point_cloud(self):
        tests = [
            [(1, 1, 0),
             [(-1, 1), (1, 1), (-2, -1), (3, -1), (0, 0), (5, 2), (-2, -3)],
             [(-2, -3), (-2, -1)], [(3, -1), (5, 2), (1, 1)]
             ]
        ]

        for line_args, s, s1_test, s2_test in tests:
            line = Line(*line_args)
            s, s1_test, s2_test = ({Coord(p) for p in coords} for coords in (s, s1_test, s2_test))
            s1, s2 = line.split_point_cloud(s)

            self.assertTrue((s1_test == s1 or s1_test == s2) and (s2_test == s1 or s2_test == s2))

    def test_intersect(self):
        tests = [
            [(1, -1, 2), (1, 0, -1), (1, 3)],
            [(-2, 2, -5), (1, -2, 1), (-4, -1.5)],
            [(3, -5, 7), (5, -8, 4), (36, 23)]
        ]

        for l1, l2, i_test in tests:
            i = Line(*l1).intersect(Line(*l2))
            self.assertEqual(i, Coord(i_test))

    def test_dist_sq(self):
        tests = [
            [(1, 1, -2), (-2, 1), 4.5],
            [(1, -3, 2), (-1, -1), 1.6],
            [(1, -3, 2), (-5, -1), 0],
            [(1, 0, 3), (1, 4), 16]
        ]

        for l, pt, dist_sq in tests:
            self.assertEqual(dist_sq, Line(*l).distance_sq(Coord(pt)))


class TestHull(unittest.TestCase):
    def test_quickhull(self):
        tests = [

            #   O O O
            #   O O .
            #   O O O
            [
                [Coord((1, 3)), Coord((2, 3)), Coord((3, 3)), Coord((1, 2)), Coord((2, 2)), Coord((1, 1)),
                 Coord((2, 1)), Coord((3, 1))],
                {Coord((1, 3)), Coord((3, 3)), Coord((1, 1)), Coord((3, 1))}
            ],

            #   O O O
            #   O O .
            #   O O O
            [
                [Coord((1, 3)), Coord((2, 3)), Coord((3, 3)), Coord((1, 2)), Coord((2, 2)), Coord((1, 1))],
                {Coord((1, 3)), Coord((3, 3)), Coord((1, 1))}
            ],

            #   O O O O .
            #   . O . O .
            #   O . O O .
            #   . . . . O
            [
                [Coord((1, 3)), Coord((2, 3)), Coord((3, 3)), Coord((4, 3)), Coord((2, 2)), Coord((4, 2)),
                 Coord((1, 1)), Coord((3, 1)), Coord((4, 1)), Coord((5, 0))],
                {Coord((1, 3)), Coord((4, 3)), Coord((1, 1)), Coord((5, 0))}
            ],

            #   O . . O .
            #   O O O O .
            #   . . O . O
            #   . O . O .
            [
                [Coord((1, 4)), Coord((4, 4)), Coord((1, 3)), Coord((2, 3)), Coord((3, 3)), Coord((4, 3)),
                 Coord((3, 2)), Coord((5, 2)), Coord((2, 1)), Coord((4, 1)), Coord((1, 0))],
                {Coord((1, 4)), Coord((4, 4)), Coord((5, 2)), Coord((4, 1)), Coord((1, 0))}
            ]
        ]

        for point_cloud, test_verts in tests:
            self.assertEqual(test_verts, Hull(point_cloud).vertices)


if __name__ == "__main__":
    unittest.main()
