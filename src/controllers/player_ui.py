from src.controllers.point_pos_bridge import to_game_coord, to_ui_coord
from src.models.action import Action
from src.models.players import Player, AIPlayer
from src.views.board_scene import BoardDelegate
from time import time


class GuiPlayer(Player):
    def __init__(self, board, player_id):
        super(GuiPlayer, self).__init__(board, player_id)
        self.board_scene = None
        self.action = None
        self.delegate = None
        self.can_act = False

        self.should_stop_execution = False

    def play(self):
        action = self._play()
        if not self.should_stop_execution:
            self.board.act(action)


class HumanGuiPlayer(GuiPlayer, BoardDelegate):
    def __init__(self, board, player_id):
        super(HumanGuiPlayer, self).__init__(board, player_id)
        self.action = None

    def _play(self):
        self.can_act = True
        self.action = None
        self.board_scene.allow_pieces_interaction(self.player_id)

        # wait until the user moves his pieces
        while self.action is None and not self.should_stop_execution:
            pass
        self.can_act = False
        self.delegate.played()

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
            # l'action est valide!
            self.board.undo()

            return True

    def perform_action(self, queen_from, queen_to, arr):
        self.action = Action(*[to_game_coord(self.board.size, pos)
                               for pos in (queen_from, queen_to, arr)], self.player_id)


class AIGuiPlayer(GuiPlayer, AIPlayer, BoardDelegate):
    def __init__(self, ai_ai_delay, *args, **kwargs):
        super(AIGuiPlayer, self).__init__(*args, **kwargs)
        self.timer.timeouts_soon_threshold = 0.15
        self.ai_ai_delay = ai_ai_delay
        self.action_start_time = None

        self.can_return_action = False

    def _play(self):
        self.action_start_time = time()
        self.board_scene.stop_all_possible_interaction()
        action = super(AIGuiPlayer, self)._play()
        self.can_return_action = False

        while not (time() - self.action_start_time >= self.ai_ai_delay or
                   self.should_stop_execution):
            pass
        self.delegate.played(action)
        while not (self.can_return_action or self.should_stop_execution):
            pass
        return action

    def piece_selected(self, coord) -> [tuple]:
        return []

    def piece_moved(self, from_coord, to_coord) -> [tuple]:
        return []

    def is_action_valid(self, queen_from, queen_to, arr) -> bool:
        return True

    def perform_action(self, queen_from, queen_to, arr):
        # attendre que la gui ait fini l'animation avant d'appliquer le coup à Amazons
        self.can_return_action = True


class GuiPlayerDelegate:
    def played(self, action):
        raise NotImplemented
