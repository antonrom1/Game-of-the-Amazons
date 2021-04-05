from src.models.amazons import Amazons
from src.models.pos2d import Pos2D
from src.views.board_view import BoardView
from src.views.board_scene import BoardDelegate
from src.views.window import MainWindow
from src.models.action import Action
from src.models.players import Player, AIPlayer
import threading
from src.const import PLAYER_1, PLAYER_2
from src.controllers.main_thread_executor import MainThreadExecutor


class HumanGuiPlayer(Player, BoardDelegate):
    def __init__(self, board, player_id):
        super(HumanGuiPlayer, self).__init__(board, player_id)
        self.board_scene = None
        self.can_act = False
        self.action = None
        self.delegate = None

    def _play(self):
        self.can_act = True
        self.action = None
        self.board_scene.allow_pieces_interaction(self.player_id)

        # wait until the user moves his pieces
        while self.action is None:
            pass

        self.can_act = False
        MainThreadExecutor.shared.run(self.delegate.played)

        return self.action


    def piece_selected(self, coord) -> [tuple]:
        queen_coord = to_game_coord(self.board.size, coord)
        moves = list(self.board._possible_moves_from(queen_coord))
        return [to_ui_coord(self.board.size, m) for m in moves]

    def piece_moved(self, from_coord, to_coord) -> [tuple]:
        queen_init_coords = to_game_coord(self.board.size, from_coord)
        queen_final_coord = to_game_coord(self.board.size, to_coord)

        possible_arr_positions = list(self.board._possible_moves_from(queen_final_coord, queen_init_coords))

        return [to_ui_coord(self.board.size, pos) for pos in possible_arr_positions]

    def is_action_valid(self, queen_from, queen_to, arr) -> bool:
        if not self.can_act:
            return False
        queen_from_bd = to_game_coord(self.board.size, queen_from)
        queen_to_bd = to_game_coord(self.board.size, queen_to)
        arr_bd = to_game_coord(self.board.size, arr)

        try:
            player = self.board.grid[queen_from_bd]
        except IndexError:
            print("Invalid queen position")
            return False

        try:
            action = Action(queen_from_bd, queen_to_bd, arr_bd, player)
        except Exception:
            print("This is not an action")
            return False

        try:
            self.board.act(action)
        except Exception:
            print("Action is invalid")
            return False
        else:
            print("Action is valid")
            self.board.undo()
            return True

    def perform_action(self, queen_from, queen_to, arr):
        self.action = Action(*[to_game_coord(self.board.size, pos)
                               for pos in (queen_from, queen_to, arr)], self.player_id)
        MainThreadExecutor.shared.run(self.delegate.switch_to_next_player, self.other_player_id)


class AIGuiPlayer(AIPlayer, BoardDelegate):
    def __init__(self, *args, **kwargs):
        super(AIGuiPlayer, self).__init__(*args, **kwargs)
        self.delegate = None
        self.can_return_action = False

    def _play(self):
        action = super(AIGuiPlayer, self)._play()
        self.can_return_action = False
        MainThreadExecutor.shared.run(self.delegate.played, action)
        while not self.can_return_action:
            pass
        return action

    def piece_selected(self, coord) -> [tuple]:
        return []

    def piece_moved(self, from_coord, to_coord) -> [tuple]:
        return []

    def is_action_valid(self, queen_from, queen_to, arr) -> bool:
        return True

    def perform_action(self, queen_from, queen_to, arr):
        MainThreadExecutor.shared.run(self.delegate.switch_to_next_player, self.other_player_id)
        self.can_return_action = True



class GuiPlayerDelegate:
    def played(self, action):
        raise NotImplemented

    def switch_to_next_player(self, next_player_id):
        raise NotImplemented


class GameViewController(BoardDelegate, GuiPlayerDelegate):
    def __init__(self, game: Amazons):
        self.game = game
        self.window = None
        self.board_view = None

        self.init_ui()

        self.window.show()

        for player in self.game.players:
            player.delegate = self
            if isinstance(player, HumanGuiPlayer):
                player.board_scene = self.board_view.board_scene

        game_logic = threading.Thread(target=self.game.play)
        game_logic.start()

    def init_ui(self):
        pieces = {}
        for queen, positions in enumerate(self.game.board.queens):
            pieces.update({to_ui_coord(self.game.board.size, pos): queen for pos in positions})

        arrows = [to_ui_coord(self.game.board.size, arr) for arr in self.game.board.arrows]

        self.board_view = BoardView(self.game.players[self.game.current_player_idx],
                                    self.game.board.size,
                                    self.window, pieces, arrows)
        self.window = MainWindow(self.board_view)

    def show_game_over_label_if_needed(self):
        if self.game.board.status.over:
            self.board_view.board_scene.dis

    # GuiPlayerDelegate protocol

    def played(self, action=None):
        if action is not None:
            bd_scene = self.board_view.board_scene
            coords = action_to_game_coords(self.game.board.size, action)
            bd_scene.perform_action(*coords)

    def switch_to_next_player(self, next_player_id):
        self.board_view.board_scene.board_delegate = self.game.players[next_player_id]


def to_ui_coord(board_size, coord):
    return board_size - coord.row - 1, coord.col


def to_game_coord(board_size, coord):
    return Pos2D(board_size - coord[0] - 1, coord[1])


def action_to_game_coords(board_size, action):
    action_coord_list = [action.old_pos, action.new_pos, action.arrow_pos]
    return [to_ui_coord(board_size, coord) for coord in action_coord_list]
