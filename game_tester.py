import numpy as np

from minesweeper import field

f = field.Field(np.array([
    [0, 0, 0, 1, 0, 0, 0],
    [1, 1, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 0, 0, 1],
    [0, 1, 1, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 1, 0, 0],
    [1, 1, 1, 1, 0, 0, 1]
]))
f.pick_square(1, 5)
