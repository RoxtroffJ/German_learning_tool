"""Buttons for selection tree. Based on tree_selection_state."""

import tkinter.ttk as ttk
from typing import Any, Generic, TypeVar

from pyparsing import Callable

from guilib import PADDING
from guilib.pages import HeaderedPage
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

_HP = TypeVar("_HP", bound=HeaderedPage[Any], covariant=True)

class HeaderedWithSelectAll(Generic[_HP], HeaderedPage[Any]):
    """A HeaderedPage with a select all button in the header."""

    def __init__(self, page: _HP, tree_selection_state: TreeSelectionState, select_all_path: Path, header_sticky: str | None = None):
        """Creates a HeaderedWithSelectAll page wrapping the given page."""
        
        self.__dict__.update(page.__dict__)
        self.__header_sticky = header_sticky or page.header_sticky

        header_frame = page.header_frame()
        header_frame.columnconfigure(0, weight=1)

        select_all_button = ttk.Button(header_frame, text="Select All", command=lambda: tree_selection_state.select_all_callback(select_all_path))
        select_all_button.grid(column=1, row=0, padx=PADDING, sticky="E")

        deselect_all_button = ttk.Button(header_frame, text="Deselect All", command=lambda: tree_selection_state.deselect_all_callback(select_all_path))
        deselect_all_button.grid(column=2, row=0, padx=(0, PADDING), sticky="E")

        stylify_button(
            select_all_button,
            tree_selection_state,
            select_all_path,
        )

        self.__sub_header_frame = ttk.Frame(header_frame)
        self.__sub_header_frame.grid(column=0, row=0, sticky=self.__header_sticky)

    @property
    def header_sticky(self) -> str:
        """Returns the header sticky."""
        return self.__header_sticky
    
    def header_frame(self):
        return self.__sub_header_frame
        