from src.models.amazons import Amazons
from src.models.pos2d import Pos2D
from src.views.board_view import BoardView
from src.views.board_scene import BoardDelegate
from src.views.window import MainWindow


class GameViewController(BoardDelegate):
    def __init__(self, game: Amazons):
        self.game = game
        self.window = None
        self.board_view = None

        self.init_ui()

        self.window.show()

    def init_ui(self):
        pieces = {}
        for queen, positions in enumerate(self.game.board.queens):
            pieces.update({self.to_ui_coord(pos): queen for pos in positions})

        self.board_view = BoardView(self, self.game.board.size, self.window, pieces)

        self.window = MainWindow(self.board_view)

    def to_ui_coord(self, coord):
        return self.game.board.size - coord.row - 1, coord.col

    def to_game_coord(self, coord):
        return Pos2D(self.game.board.size - coord[0] - 1, coord[1])

    def piece_selected(self, coord) -> [tuple]:
        queen_coord = self.to_game_coord(coord)
        moves = list(self.game.board._possible_moves_from(queen_coord))
        moves_bd = [self.to_ui_coord(m) for m in moves]
        return moves_bd
