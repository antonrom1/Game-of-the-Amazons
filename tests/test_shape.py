import unittest
from src.geometry import Coord
from src.shape import Shape


class TestShape(unittest.TestCase):
    def test_lines(self):
        tests = [
            [[Coord((1, 4)), Coord((2, 3)), Coord((3, 2)), Coord((4, 1))], True],
            [[Coord((1, 4)), Coord((2, 3)), Coord((3, 2)), Coord((4, 2))], False],
            [[Coord((1, 2)), Coord((2, 2)), Coord((3, 2)), Coord((4, 2))], True],
            [[Coord((1, 1))], False],
            [[Coord((1, 2)), Coord((1, 1))], True],
            [[Coord((1, 2)), Coord((2, 1))], True],
            [[Coord((1, 2)), Coord((3, 2)), Coord((2, 1))], False]
        ]

        for line, valid in tests:
            if valid:
                self.assertEqual(Shape.LINE, Shape.get_shape(line))
            else:
                self.assertNotEqual(Shape.LINE, Shape.get_shape(line))

    def test_rect(self):
        tests = [
            [[Coord((1, 2)), Coord((2, 2)), Coord((3, 2)), Coord((1, 1)), Coord((2, 1)), Coord((3, 1))], True],

            [[Coord((1, 2)), Coord((1, 1))], False],

            [[Coord((1, 2)), Coord((1, 1)), Coord((2, 1))], False],

            [[Coord((1, 2)), Coord((1, 1)), Coord((2, 1)), Coord((2, 0))], False],

            [[Coord((1, 3)), Coord((2, 3)), Coord((1, 2)), Coord((2, 2)), Coord((1, 1)), Coord((2, 1))], True],

            [[Coord((1, 4)), Coord((2, 4)), Coord((1, 3)), Coord((2, 3))], True],

            [[Coord((0, 5)), Coord((1, 5)), Coord((2, 5)), Coord((3, 5)), Coord((4, 5)), Coord((5, 5)), Coord((0, 4)),
              Coord((1, 4)), Coord((2, 4)), Coord((3, 4)), Coord((4, 4)), Coord((5, 4)), Coord((0, 3)), Coord((1, 3)),
              Coord((2, 3)), Coord((3, 3)), Coord((4, 3)), Coord((5, 3)), Coord((0, 2)), Coord((1, 2)), Coord((2, 2)),
              Coord((3, 2)), Coord((4, 2)), Coord((5, 2)), Coord((0, 1)), Coord((1, 1)), Coord((2, 1)), Coord((3, 1)),
              Coord((4, 1)), Coord((5, 1)), Coord((0, 0)), Coord((1, 0)), Coord((2, 0)), Coord((3, 0)), Coord((4, 0)),
              Coord((5, 0))],
             True]
        ]

        for rect, valid in tests:
            if valid:
                self.assertEqual(Shape.RECT, Shape.get_shape(rect))
            else:
                self.assertNotEqual(Shape.RECT, Shape.get_shape(rect))

    def test_trig(self):
        tests = [
            [[Coord((2, 4)), Coord((1, 3)), Coord((3, 3))], False],
            [[Coord((2, 4)), Coord((1, 3)), Coord((2, 3)), Coord((3, 3))], True],
            [[Coord((1, 5)), Coord((1, 4)), Coord((2, 4)), Coord((1, 3)), Coord((2, 3)), Coord((3, 3))], True],
            [[Coord((2, 4)), Coord((2, 3)), Coord((3, 3))], True],
            [[Coord((2, 4)), Coord((2, 3)), Coord((3, 3)), Coord((2, 2))], True],
            [[Coord((2, 4)), Coord((1, 3)), Coord((2, 3)), Coord((3, 3)), Coord((2, 2))], False],
            [[Coord((2, 4)), Coord((1, 3)), Coord((2, 3)), Coord((3, 3)), Coord((0, 2)), Coord((1, 2)),
              Coord((2, 2)), Coord((3, 2)), Coord((4, 2))], True],
            [[Coord((2, 4)), Coord((2, 3)), Coord((3, 3)), Coord((2, 2)), Coord((3, 2)), Coord((4, 2))], True],
            [[Coord((2, 4)), Coord((2, 3)), Coord((3, 3)), Coord((2, 2)), Coord((3, 2)), Coord((4, 2)),
              Coord((2, 1)), Coord((3, 1)), Coord((2, 0))], True]
        ]

        for trig, valid in tests:
            if valid:
                self.assertEqual(Shape.TRIG, Shape.get_shape(trig))
            else:
                self.assertNotEqual(Shape.TRIG, Shape.get_shape(trig))


if __name__ == "__main__":
    unittest.main()
