from itertools import product
import time

import numpy as np
from scipy.ndimage import convolve


def initialize_mines(rows, cols, mine_ratio):
    total_squares = rows * cols
    num_mines = round(total_squares * mine_ratio)
    mines = np.array(
        [1] * num_mines + [0] * (total_squares - num_mines)
    )
    np.random.seed(int(time.time()))
    np.random.shuffle(mines)

    return np.reshape(mines, (rows, cols))


def generate_adjacency_matrix(mines):
    """
    Given the minefield, generate the adjacency matrix, 
    which shows for each non-mined square how many mines 
    are next to it.
    """
    return convolve(
        mines,
        np.ones((3, 3), dtype=int),
        mode='constant',
        cval=0
    ).astype(int)


def reveal_square(flagged, adjacency_matrix, revealed, row_idx, col_idx, auto_reveal):
    """
    Emulates the behavior of clicking on a square in minesweeper. Behavior varies
    based on the value of ``auto_reveal``.

    If ``auto_reveal`` is set to False, it will only auto-reveal squares if the 
    picked square has 0 adjacent mines.

    If ``auto_reveal`` is set to True, it will auto-reveal squares if the picked
    square has the appropriate number of mines flagged.   
    """
    num_rows, num_cols = flagged.shape

    to_check = [(row_idx, col_idx)]
    already_checked = set()
    update_matrix = np.zeros(flagged.shape, dtype=int)
    update_matrix[row_idx, col_idx] = 1

    if not auto_reveal and adjacency_matrix[row_idx, col_idx] != 0:
        return update_matrix

    while len(to_check) > 0:
        curr_row, curr_col = to_check.pop()
        already_checked.add((curr_row, curr_col))
        adjacent_squares = set(product(
            np.clip(np.arange(curr_row - 1, curr_row + 2), 0, num_rows - 1, dtype=int),
            np.clip(np.arange(curr_col - 1, curr_col + 2), 0, num_cols - 1, dtype=int)
        ))

        row_indexer, col_indexer = np.array(list(adjacent_squares)).T
        adjacent_flagged = flagged[row_indexer, col_indexer]

        # If number of adjacent flags is equal to or less than indicated number of
        # adjacent mines, reveal the unflagged neighbors as well. We are essentially
        # performing a breadth-first search here.
        if sum(adjacent_flagged) >= adjacency_matrix[curr_row, curr_col]:
            for coord in zip(row_indexer, col_indexer):
                can_add = (
                    (coord not in already_checked) and
                    not revealed[coord] and
                    not flagged[coord]
                )

                if can_add:
                    to_check.append(coord)
        update_matrix[curr_row, curr_col] = 1

    return update_matrix


def update_revelation_matrix(mines, flagged, adjacency_matrix, revealed, row_idx, col_idx):
    """
    Given the picked square, update the revelation matrix
    accordingly. This assumes that the picked square is 
    not mined. Of course, never reveal an actual mine when
    doing this.
    """
    to_test = list(product(
        range(row_idx - 1, row_idx + 2), 
        range(col_idx - 1, col_idx + 2)
    ))
    rows, cols = adjacency_matrix.shape
    checked = set((row_idx, col_idx))

    # Perform a depth-first search of the minefield.
    update_matrix = np.zeros_like(revealed)
    while len(to_test) > 0:
        item = to_test.pop()
        curr_row, curr_col = item
        # First check if square is in bounds.
        if (curr_row < 0 or curr_row >= rows) or (curr_col < 0 or curr_col >= cols):
            checked.add((curr_row, curr_col))
            continue
        # Then check if already revealed.
        elif revealed[curr_row, curr_col]:
            checked.add((curr_row, curr_col))
            continue
        
        # If the square has the appropriate number of neighboring mines 
        # flagged, reveal this square and its neighbors, even if one
        # of those squares has a mine on it.
        if adjacency_matrix[curr_row, curr_col] == 0:
            update_matrix[curr_row, curr_col] = 1
            to_test.extend([
                coord for coord in product(
                    range(curr_row - 1, curr_row + 2),
                    range(curr_col - 1, curr_col + 2)
                )
                if coord not in checked
            ])
        elif mines[curr_row, curr_col] or flagged[curr_row, curr_col]:
            pass # Do not reveal this square.
        else:
            update_matrix[curr_row, curr_col] = 1
        
        checked.add((curr_row, curr_col))
    
    return update_matrix


class Field:

    def __init__(self, num_rows, num_cols, mine_ratio):
        self.rows, self.cols = num_rows, num_cols
        self.mine_ratio = mine_ratio

        self._revealed = np.zeros((num_rows, num_cols), dtype=int)
        self._mines = None
        self._adjacency_matrix = None
        self._flagged = np.zeros_like(self._revealed)

    @classmethod
    def from_mine_matrix(cls, mines):
        """
        Directly initialize with a mine matrix. Useful for testing
        purposes.
        """
        rows, cols = mines.shape
        mine_ratio = float(np.sum(mines) / float(rows * cols))
        to_return = cls(
            num_rows=rows,
            num_cols=cols,
            mine_ratio=mine_ratio
        )
        to_return._mines = np.array(mines)
        to_return.adjacency_matrix = generate_adjacency_matrix(mines)

        return to_return

    @property
    def initialized(self):
        return self._adjacency_matrix is not None and self._mines is not None

    def _initialize(self, row_idx, col_idx):
        """Ensure that the first pick does not kill the player."""
        self._mines = initialize_mines(self.rows, self.cols, self.mine_ratio)
        while self._mines[row_idx, col_idx]:
            self._mines = initialize_mines(self.rows, self.cols, self.mine_ratio)
        self._adjacency_matrix = generate_adjacency_matrix(self._mines)

    def pick_square(self, row_idx, col_idx, auto_reveal):
        """
        Pick a square. Updates the internal revalation matrix and also 
        returns whether or not this pick detonated a mine.
        """

        if not self.initialized:
            self._initialize(row_idx, col_idx)

        revelation_update = reveal_square(
            flagged=self._flagged,
            adjacency_matrix=self._adjacency_matrix,
            revealed=self._revealed,
            row_idx=row_idx, 
            col_idx=col_idx,
            auto_reveal=auto_reveal
        )
        self._revealed |= revelation_update

        # If we revealed any mines, fail the game.
        return not np.any(self._mines * self._revealed)

    def toggle_flag_square(self, row_idx, col_idx):
        """
        Toggle flag on the given square. If the square is already revealed,
        don't do anything.
        """
        if not self._revealed[row_idx, col_idx]:
            self._flagged[row_idx, col_idx] = (self._flagged[row_idx, col_idx] + 1) % 2

    @property
    def revealed(self):
        return self._revealed
    
    @property
    def mines(self):
        return self._mines
    
    @property
    def adjacency_matrix(self):
        return self._adjacency_matrix
    
    @property
    def flagged(self):
        return self._flagged
