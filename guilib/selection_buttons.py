"""Buttons for selection tree. Based on tree_selection_state."""

import tkinter.ttk as ttk

from pyparsing import Callable

from guilib.tree_selection_state import *

def stylify_button(btn: ttk.Button, state: TreeSelectionState, path: Path, label_format: Callable[[bool, int], str] | None = None):
    """Applies styling to btn based on state at path."""
    
    def callback(selected: bool, nb_selected: int):
        if label_format is not None:
            btn.config(text=label_format(selected, nb_selected))
        if selected:
            btn.config(style="Success.TButton")
        elif nb_selected > 0:
            btn.config(style="OutlineSuccess.TButton")
        else:
            btn.config(style="")
    
    state.set_double_callback(path, callback)
    
    # Initialize

    (selected, nb_selected) = state.get(path)
    callback(selected, nb_selected)

