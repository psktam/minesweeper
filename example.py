from prompt_toolkit import application
from prompt_toolkit.keys import Keys
from prompt_toolkit import key_binding
from prompt_toolkit.layout import Layout, Window
from prompt_toolkit.layout.controls import UIContent, UIControl

import colorama

kb = key_binding.KeyBindings()


_DOC_CONTENT = [
    [("", "Last button pressed: ")],
    [("", "")]
]


def get_line(line_no):
    global _DOC_CONTENT
    return list(_DOC_CONTENT)[line_no]




class Control(UIControl):
    def create_content(self, width: int, height: int) -> UIContent:
        return UIContent(
            get_line=get_line,
            line_count=2
        )



@kb.add(Keys.Any, filter=True, is_global=True)
def handler(event):
    global _DOC_CONTENT
    _DOC_CONTENT[1] = [("", f"Some generic keystroke: {str(event)}")]

@kb.add(Keys.Up, filter=True, is_global=True)
@kb.add(Keys.Down, filter=True, is_global=True)
@kb.add(Keys.Right, filter=True, is_global=True)
@kb.add(Keys.Left, filter=True, is_global=True)
def arrows(event):
    global _DOC_CONTENT
    _DOC_CONTENT[1] = [
        ("", "Pressed an arrow key instead: "),
        ("bg:ansigreen fg:ansiblack", str(event))
    ]


if __name__ == "__main__":
    app = application.Application(
        layout=Layout(
            Window(content=Control(), width=800, height=600)
        ), 
        key_bindings=kb
    )

    @kb.add(Keys.ControlC)
    def quit_game(event):
        app.exit()

    app.run()
