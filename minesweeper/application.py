from enum import Enum
from prompt_toolkit import application
from prompt_toolkit import key_binding
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout, Window
from prompt_toolkit.layout.controls import UIContent, UIControl

import numpy as np

from .field import Field, initialize_mines
from . import icons


class GameStatus(Enum):
    Playing = "playing"
    Lost = "loooosssseeerrr"
    Won = "winnar"


def render_field(field: Field):
    representation = []
    for row_idx in range(field.rows):
        row_chars = []
        for col_idx in range(field.cols):
            if not field.revealed[row_idx, col_idx]:
                if field.flagged[row_idx, col_idx]:
                    row_chars.append(icons.FLAG)
                else:
                    row_chars.append(icons.UNKNOWN)
            elif field.mines[row_idx, col_idx]:
                row_chars.append(icons.MINE)
            elif field.adjacency_matrix[row_idx, col_idx] == 0:
                row_chars.append(icons.BLANK)
            else:
                row_chars.append(str(field.adjacency_matrix[row_idx, col_idx]))
        
        representation.append(row_chars)
    return representation


def _convert_to_ptkit_representation(raw_representation, cursor_row, cursor_col, auto_reveal_enabled):
    """
    Convert intermediate field representation into one that prompt toolkit
    understands.
    """
    as_lines = [' '.join(line) for line in raw_representation]

    # Convert into those style/string tuples:
    ptkit_lines = [
        [("", line)]
        for line in as_lines
    ]

    _highlight_cursor_location(
        cursor_row, 
        cursor_col, 
        "fg:ansiblack bg:ansigreen", 
        as_lines, 
        ptkit_lines
    )

    full_content = (
        _generate_instruction_header(auto_reveal_enabled) + 
        ptkit_lines
    )

    return full_content


def _highlight_cursor_location(cursor_row, cursor_col, cursor_style, prerendered, rendered):
    cursor_line = prerendered[cursor_row]
    line_idx = cursor_col * 2
    head = cursor_line[:line_idx]
    cursor_char = cursor_line[line_idx]
    tail = cursor_line[line_idx + 1:]
    new_line = [
        ("", head),
        (cursor_style, cursor_char),
        # ("fg:ansiblack bg:ansigreen", cursor_char),
        ("", tail)
    ]
    rendered[cursor_row] = new_line


def _generate_instruction_header(auto_reveal_enabled):
    return [
        [("", "Instructions")],
        [("", "------------")],
        [("", "f: set/unset flag")],
        [("", "x: expose single square" if not auto_reveal_enabled else "x: auto-reveal squares (like middle-clicking)")],
        [("", "q: toggle auto-reveal")],
        [("", "<arrow keys> or <h,j,k,l>: move the cursor around")],
        [("", "Ctrl-C: quit game")],
        [("", "")]
    ]


def render_death_screen(minefield, cursor_row, cursor_col, auto_reveal_enabled):
    """Show the death screen."""
    header = _generate_instruction_header(auto_reveal_enabled)
    prerendered = [" ".join(f" {icons.MINE}"[flag] for flag in row) for row in minefield]
    rendered = [[("", line)] for line in prerendered]
    _highlight_cursor_location(cursor_row, cursor_col, "fg:ansiwhite bg:ansired", prerendered, rendered)

    rendered.extend([
        [("", "")],
        [("", "Owie-wowie, you died :(")]
    ])
    return header + rendered


_KEYBINDINGS = key_binding.KeyBindings()


class FieldController(UIControl):

    def __init__(self, field: Field):
        self._status = GameStatus.Playing
        self._field = field
        self._cursor_row = 0
        self._cursor_col = 0
        self._auto_reveal = False

        _KEYBINDINGS.add(Keys.Up)(lambda _: self._move_cursor_up())
        _KEYBINDINGS.add(Keys.Down)(lambda _: self._move_cursor_down())
        _KEYBINDINGS.add(Keys.Right)(lambda _: self._move_cursor_right())
        _KEYBINDINGS.add(Keys.Left)(lambda _: self._move_cursor_left())
        _KEYBINDINGS.add(Keys.Any)(self.handle_action)

    def _move_cursor_up(self):
        self._cursor_row = max(0, self._cursor_row - 1)

    def _move_cursor_down(self):
        self._cursor_row = min(self._cursor_row + 1, self._field.rows - 1)

    def _move_cursor_left(self):
        self._cursor_col = max(0, self._cursor_col - 1)

    def _move_cursor_right(self):
        self._cursor_col = min(self._cursor_col + 1, self._field.cols - 1)
        
    def handle_action(self, event):
        key = event.key_sequence[0].key
        if key == 'f':
            self._field.toggle_flag_square(self._cursor_row, self._cursor_col)
        elif key == 'x':
            if not self._field.pick_square(self._cursor_row, self._cursor_col, auto_reveal=self._auto_reveal):
                self._status = GameStatus.Lost
        elif key == 'h':
            self._move_cursor_left()
        elif key == 'j':
            self._move_cursor_down()
        elif key == 'k': 
            self._move_cursor_up()
        elif key == 'l':
            self._move_cursor_right()
        elif key == 'q':
            self._auto_reveal = not self._auto_reveal

    def evaluate_win_condition(self):
        """
        The game is won when the inverse of the revelation matrix exactly 
        matches the mine matrix.
        """
        if self._status == GameStatus.Lost:
            return
        
        if not self._field.initialized:
            return

        revealed = ~self._field.revealed.astype(bool)
        mined = self._field.mines.astype(bool)
        if np.all(mined == revealed):
            self._status = GameStatus.Won

    def create_content(self, width: int, height: int) -> UIContent:
        self.evaluate_win_condition()

        if self._status == GameStatus.Lost:
            death = render_death_screen(self._field.mines, self._cursor_row, self._cursor_col, self._auto_reveal)
            return UIContent(
                get_line=lambda line_no: death[line_no],
                line_count=len(death)
            )
        elif self._status == GameStatus.Won:
            return UIContent(
                get_line=lambda line_no: [[("", "u r winner!")]][line_no],
                line_count=1
            )

        field_repr = render_field(self._field)
        full_content = _convert_to_ptkit_representation(field_repr, self._cursor_row, self._cursor_col, self._auto_reveal)

        return UIContent(
            get_line=lambda line_no: full_content[line_no],
            line_count=len(full_content)
        )


def create_app(rows, cols, mine_ratio):
    field = Field(num_rows=rows, num_cols=cols, mine_ratio=mine_ratio)
    main_control = FieldController(field)
    app = application.Application(
        layout=Layout(
            Window(content=main_control, width=800, height=600)
        ),
        key_bindings=_KEYBINDINGS
    )

    @_KEYBINDINGS.add(Keys.ControlC)
    def quit_game(event):
        app.exit()

    return app
