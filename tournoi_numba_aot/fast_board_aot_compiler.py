import numpy as np
from numba.pycc import CC
from numba import njit

cc = CC("fast_board")

@njit
@cc.export('possible_moves', 'int8[:, :](int8[:, :], int8, int16, boolean[:, :], int8[:], int8[:, :, :, :], boolean)')
def possible_moves(DIR, N, num_tiles, empty_cells, from_pos, cache, return_first_found):
    if cache[from_pos[0], from_pos[1], 0, 0] != -1:
        cached_res = cache[from_pos[0], from_pos[1]]
        until_idx = np.argmax(cached_res[:, 0] == -1)
        return cache[from_pos[0], from_pos[1], :until_idx]

    moves = np.empty((num_tiles, 2), dtype=np.int8)
    moves_idx = 0
    for d in DIR:
        curr_pos = np.copy(from_pos)

        while True:
            curr_pos += d
            if not (0 <= curr_pos[0] < N and 0 <= curr_pos[1] < N):
                break

            if empty_cells[curr_pos[0], curr_pos[1]]:
                if return_first_found:
                    return curr_pos.reshape(1, 2)
                moves[moves_idx] = curr_pos
                moves_idx += 1
            else:
                break
    final_moves = moves[:moves_idx]
    if not return_first_found:
        cache[from_pos[0], from_pos[1], :moves_idx] = final_moves
    return final_moves


@njit
@cc.export('possible_moves_ignore_pos', 'int8[:, :](int8[:, :], int8, int16, boolean[:, :], int8[:], int8[:], boolean)')
def possible_moves_ignore_pos(DIR, N, num_tiles, empty_cells, from_pos, ignore_pos, return_first_found):
    moves = np.empty((num_tiles, 2), dtype=np.int8)
    moves_idx = 0
    for d in DIR:
        curr_pos = np.copy(from_pos)

        while True:
            curr_pos += d
            if not (0 <= curr_pos[0] < N and 0 <= curr_pos[1] < N):
                break
            if np.all(curr_pos == ignore_pos) or empty_cells[curr_pos[0], curr_pos[1]]:
                if return_first_found:
                    return curr_pos.reshape(1, 2)
                moves[moves_idx] = curr_pos
                moves_idx += 1
            else:
                break
    return moves[:moves_idx]


@cc.export('reachability_grid', 'int8[:, :](int8[:, :], int8, int8[:, :], int16, boolean[:, :], int8[:, :, :, :], '
                                'int8[:, :], int16, )')
def reachability_grid(grid, N, DIR, num_tiles, empty_cells, moves_cache, prev_added,
                               prev_added_idx):
    reachability_grid = np.zeros_like(grid, dtype=np.int8)

    reachability = 1

    new_positions = np.empty_like(prev_added, dtype=np.int8)
    new_positions_idx = 0

    while prev_added_idx != 0:
        for from_pos in prev_added[:prev_added_idx]:
            moves = possible_moves(DIR, N, num_tiles, empty_cells, from_pos, moves_cache, False)
            for pos_i, pos_j in moves:
                if reachability_grid[pos_i, pos_j] == 0:
                    reachability_grid[pos_i, pos_j] = reachability
                    new_positions[new_positions_idx] = pos_i, pos_j
                    new_positions_idx += 1
        reachability += 1
        prev_added[:new_positions_idx] = new_positions[:new_positions_idx]
        prev_added_idx = new_positions_idx
        new_positions_idx = 0
    return reachability_grid


@cc.export('possible_actions', 'int8[:, :, :]('
                                'int8[:, :], '
                                'int8, '
                                'int16, '
                                'boolean[:, :], '
                                'int8[:, :], '
                                'int8[:, :, :, :], '
                                'boolean'
                                ')'
           )
def possible_actions_numba(DIR, N, num_tiles, empty_cells, queens, cache, return_first_found):
    actions = np.empty((num_tiles ** 2, 3, 2), dtype=np.int8)
    actions_idx = 0
    for queen in queens:
        for queen_move in possible_moves(DIR, N, num_tiles, empty_cells, queen, cache, False):
            for arr_move in possible_moves_ignore_pos(DIR, N, num_tiles, empty_cells, queen_move, queen,
                                                                 return_first_found):
                actions[actions_idx, 0] = queen
                actions[actions_idx, 1] = queen_move
                actions[actions_idx, 2] = arr_move
                actions_idx += 1

                if return_first_found:
                    return actions[:1]
    return actions[:actions_idx]


def compile():
    cc.compile()

if __name__ == "__main__":
    compile()

